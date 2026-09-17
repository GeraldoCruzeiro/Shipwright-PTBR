#include "PTBRVoice.h"

#include "PTBRData.h"

#include "global.h"
#include "soh/Enhancements/game-interactor/GameInteractor.h"
#include "soh/ShipInit.hpp"

#include <SDL2/SDL.h>
#include <ship/Context.h>
#include <spdlog/spdlog.h>

#include <cstdint>
#include <filesystem>
#include <iomanip>
#include <sstream>
#include <string>

extern "C" {
extern PlayState* gPlayState;
}

namespace {

SDL_AudioDeviceID sVoiceDevice = 0;
SDL_AudioSpec sVoiceDeviceSpec = {};

bool sTrackingMessage = false;
bool sPendingPage = false;
bool sHasPlayedPage = false;
uint16_t sCurrentTextId = 0;
uint16_t sCurrentPage = 0;

bool EnsureVoiceDevice() {
    if (sVoiceDevice != 0) {
        return true;
    }

    if ((SDL_WasInit(SDL_INIT_AUDIO) & SDL_INIT_AUDIO) == 0) {
        if (SDL_InitSubSystem(SDL_INIT_AUDIO) != 0) {
            SPDLOG_ERROR("[PTBR Voice] Falha ao iniciar SDL audio: {}", SDL_GetError());
            return false;
        }
    }

    SDL_AudioSpec wanted = {};
    wanted.freq = 44100;
    wanted.format = AUDIO_S16SYS;
    wanted.channels = 2;
    wanted.samples = 1024;
    wanted.callback = nullptr;

    sVoiceDevice = SDL_OpenAudioDevice(
        nullptr,
        0,
        &wanted,
        &sVoiceDeviceSpec,
        SDL_AUDIO_ALLOW_ANY_CHANGE
    );

    if (sVoiceDevice == 0) {
        SPDLOG_ERROR("[PTBR Voice] Falha ao abrir dispositivo de voz: {}", SDL_GetError());
        return false;
    }

    SDL_PauseAudioDevice(sVoiceDevice, 0);

    SPDLOG_INFO(
        "[PTBR Voice] Dispositivo iniciado: {} Hz, {} canais, formato 0x{:X}",
        sVoiceDeviceSpec.freq,
        sVoiceDeviceSpec.channels,
        static_cast<unsigned int>(sVoiceDeviceSpec.format)
    );

    return true;
}

std::string BuildVoiceRelativePath(uint16_t textId, uint16_t page) {
    std::ostringstream filename;
    filename
        << "voices/ptbr/"
        << std::uppercase
        << std::hex
        << std::setw(4)
        << std::setfill('0')
        << textId
        << "_"
        << std::dec
        << std::setw(2)
        << std::setfill('0')
        << page
        << ".wav";

    return filename.str();
}

bool PlayVoiceFile(uint16_t textId, uint16_t page) {
    PTBRVoice_Stop();

    const std::string relativePath = BuildVoiceRelativePath(textId, page);
    const std::string fullPath =
        Ship::Context::GetPathRelativeToAppDirectory(relativePath);

    if (!std::filesystem::exists(fullPath)) {
        SPDLOG_TRACE(
            "[PTBR Voice] Sem arquivo para textId=0x{:04X}, pagina={}: {}",
            textId,
            page,
            fullPath
        );
        return false;
    }

    if (!EnsureVoiceDevice()) {
        return false;
    }

    SDL_AudioSpec sourceSpec = {};
    Uint8* sourceBuffer = nullptr;
    Uint32 sourceLength = 0;

    if (SDL_LoadWAV(
            fullPath.c_str(),
            &sourceSpec,
            &sourceBuffer,
            &sourceLength
        ) == nullptr) {
        SPDLOG_ERROR(
            "[PTBR Voice] Falha ao carregar WAV {}: {}",
            fullPath,
            SDL_GetError()
        );
        return false;
    }

    SDL_AudioCVT cvt = {};

    const int cvtResult = SDL_BuildAudioCVT(
        &cvt,
        sourceSpec.format,
        sourceSpec.channels,
        sourceSpec.freq,
        sVoiceDeviceSpec.format,
        sVoiceDeviceSpec.channels,
        sVoiceDeviceSpec.freq
    );

    if (cvtResult < 0) {
        SPDLOG_ERROR(
            "[PTBR Voice] Falha ao preparar conversao de audio {}: {}",
            fullPath,
            SDL_GetError()
        );
        SDL_FreeWAV(sourceBuffer);
        return false;
    }

    bool queued = false;

    if (cvtResult == 0) {
        queued =
            SDL_QueueAudio(sVoiceDevice, sourceBuffer, sourceLength) == 0;
    } else {
        cvt.len = static_cast<int>(sourceLength);
        cvt.buf = static_cast<Uint8*>(
            SDL_malloc(static_cast<size_t>(sourceLength) * cvt.len_mult)
        );

        if (cvt.buf == nullptr) {
            SPDLOG_ERROR(
                "[PTBR Voice] Memoria insuficiente para converter {}",
                fullPath
            );
            SDL_FreeWAV(sourceBuffer);
            return false;
        }

        SDL_memcpy(cvt.buf, sourceBuffer, sourceLength);

        if (SDL_ConvertAudio(&cvt) == 0) {
            queued =
                SDL_QueueAudio(
                    sVoiceDevice,
                    cvt.buf,
                    static_cast<Uint32>(cvt.len_cvt)
                ) == 0;
        } else {
            SPDLOG_ERROR(
                "[PTBR Voice] Falha ao converter WAV {}: {}",
                fullPath,
                SDL_GetError()
            );
        }

        SDL_free(cvt.buf);
    }

    SDL_FreeWAV(sourceBuffer);

    if (!queued) {
        SPDLOG_ERROR(
            "[PTBR Voice] Falha ao enfileirar WAV {}: {}",
            fullPath,
            SDL_GetError()
        );
        return false;
    }

    SPDLOG_INFO(
        "[PTBR Voice] Tocando textId=0x{:04X}, pagina={}: {}",
        textId,
        page,
        relativePath
    );

    return true;
}

bool IsPageTransition(const MessageContext* msgCtx) {
    if (msgCtx == nullptr) {
        return false;
    }

    return
        msgCtx->msgMode == MSGMODE_TEXT_NEXT_MSG ||
        (msgCtx->msgMode == MSGMODE_TEXT_CONTINUING &&
         msgCtx->stateTimer == 1);
}

bool IsPageReady(const MessageContext* msgCtx) {
    if (msgCtx == nullptr) {
        return false;
    }

    switch (msgCtx->msgMode) {
        case MSGMODE_TEXT_DISPLAYING:
        case MSGMODE_TEXT_AWAIT_NEXT:
        case MSGMODE_TEXT_AWAIT_INPUT:
        case MSGMODE_TEXT_DONE:
        case MSGMODE_TEXT_DELAYED_BREAK:
            return true;
        default:
            return false;
    }
}

void PTBRVoice_OnOpenText(
    uint16_t* textId,
    bool* loadFromMessageTable
) {
    (void)loadFromMessageTable;

    PTBRVoice_Stop();

    sTrackingMessage = textId != nullptr;
    sPendingPage = sTrackingMessage;
    sHasPlayedPage = false;
    sCurrentPage = 0;
    sCurrentTextId = textId != nullptr ? *textId : 0;
}

void PTBRVoice_OnDialogMessage() {
    if (!sTrackingMessage || gPlayState == nullptr) {
        return;
    }

    MessageContext* msgCtx = &gPlayState->msgCtx;

    if (IsPageTransition(msgCtx)) {
        if (!sPendingPage) {
            PTBRVoice_Stop();
        }

        sPendingPage = true;
    }

    if (sPendingPage && IsPageReady(msgCtx)) {
        if (sHasPlayedPage) {
            ++sCurrentPage;
        }

        sCurrentTextId = msgCtx->textId;

        if (PTBR_FindMessage(sCurrentTextId) != nullptr) {
            PlayVoiceFile(sCurrentTextId, sCurrentPage);
        }

        sHasPlayedPage = true;
        sPendingPage = false;
    }

    if (
        msgCtx->msgMode == MSGMODE_TEXT_CLOSING ||
        msgCtx->msgMode == MSGMODE_NONE
    ) {
        PTBRVoice_Stop();
        sTrackingMessage = false;
        sPendingPage = false;
        sHasPlayedPage = false;
    }
}

} // namespace

void PTBRVoice_Stop() {
    if (sVoiceDevice == 0) {
        return;
    }

    SDL_ClearQueuedAudio(sVoiceDevice);
}

void RegisterPTBRVoice() {
    GameInteractor::Instance
        ->RegisterGameHook<GameInteractor::OnOpenText>(
            PTBRVoice_OnOpenText
        );

    GameInteractor::Instance
        ->RegisterGameHook<GameInteractor::OnDialogMessage>(
            PTBRVoice_OnDialogMessage
        );

    GameInteractor::Instance
        ->RegisterGameHook<GameInteractor::OnExitGame>(
            [](int32_t) {
                PTBRVoice_Stop();
                sTrackingMessage = false;
                sPendingPage = false;
                sHasPlayedPage = false;
            }
        );
}

static RegisterShipInitFunc
    ptbrVoiceInit(RegisterPTBRVoice);
