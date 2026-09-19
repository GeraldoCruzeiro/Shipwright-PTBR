#include "PTBRVoice.h"

#include "PTBRData.h"

#include "global.h"
#include "overlays/actors/ovl_En_Hy/z_en_hy.h"
#include "overlays/actors/ovl_En_Ko/z_en_ko.h"
#include "overlays/actors/ovl_En_Ossan/z_en_ossan.h"
#include "overlays/actors/ovl_En_Poh/z_en_poh.h"
#include "overlays/actors/ovl_En_Tg/z_en_tg.h"
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

Actor* FindActorById(int16_t actorId) {
    if (gPlayState == nullptr) {
        return nullptr;
    }

    for (int32_t category = 0; category < ACTORCAT_MAX; ++category) {
        for (Actor* actor = gPlayState->actorCtx.actorLists[category].head;
             actor != nullptr;
             actor = actor->next) {
            if (actor->id == actorId && actor->update != nullptr) {
                return actor;
            }
        }
    }

    return nullptr;
}

Actor* FindActorByTextId(uint16_t textId) {
    if (gPlayState == nullptr) {
        return nullptr;
    }

    for (int32_t category = 0; category < ACTORCAT_MAX; ++category) {
        for (Actor* actor = gPlayState->actorCtx.actorLists[category].head;
             actor != nullptr;
             actor = actor->next) {
            if (actor->update != nullptr && actor->textId == textId) {
                return actor;
            }
        }
    }

    return nullptr;
}

Actor* ResolveActiveTalkActor(uint16_t textId) {
    if (gPlayState == nullptr) {
        return nullptr;
    }

    MessageContext* msgCtx = &gPlayState->msgCtx;
    if (msgCtx->talkActor != nullptr && msgCtx->talkActor->update != nullptr) {
        return msgCtx->talkActor;
    }

    Player* player = GET_PLAYER(gPlayState);
    if (player != nullptr && player->talkActor != nullptr &&
        player->talkActor->update != nullptr) {
        return player->talkActor;
    }

    return FindActorByTextId(textId);
}

const char* ResolveShopkeeperSpeaker(Actor* actor) {
    if (actor == nullptr || actor->id != ACTOR_EN_OSSAN) {
        actor = FindActorById(ACTOR_EN_OSSAN);
    }

    if (actor == nullptr) {
        return nullptr;
    }

    switch (actor->params & 0xFF) {
        case OSSAN_TYPE_KOKIRI:
            return "npc_masculino";
        case OSSAN_TYPE_KAKARIKO_POTION:
        case OSSAN_TYPE_MARKET_POTION:
            return "dono_loja_pocoes";
        case OSSAN_TYPE_BOMBCHUS:
            return "dono_loja_bombchu";
        case OSSAN_TYPE_BAZAAR:
            return "dono_bazaar";
        case OSSAN_TYPE_ADULT:
            return "npc_masculino";
        case OSSAN_TYPE_TALON:
            return "talon";
        case OSSAN_TYPE_ZORA:
        case OSSAN_TYPE_GORON:
            return "npc_masculino";
        case OSSAN_TYPE_INGO:
            return "ingo";
        case OSSAN_TYPE_MASK:
            return "vendedor_mascaras";
        default:
            return nullptr;
    }
}

const char* ResolveNpcGenderSpeaker(Actor* actor) {
    if (actor == nullptr) {
        return nullptr;
    }

    // Cucco Lady tambem reutiliza 0x711A, que aparece em conjuntos
    // de reacao de mascara masculinos e femininos.
    if (actor->id == ACTOR_EN_NIW_GIRL) {
        return "npc_feminino";
    }

    if (actor->id == ACTOR_EN_KO) {
        const int32_t type = actor->params & 0xFF;

        if (type == ENKO_TYPE_CHILD_FADO) {
            return "fado";
        }

        switch (type) {
            case ENKO_TYPE_CHILD_1:
            case ENKO_TYPE_CHILD_5:
            case ENKO_TYPE_CHILD_6:
            case ENKO_TYPE_CHILD_9:
            case ENKO_TYPE_CHILD_10:
                return "npc_feminino";
            default:
                return "npc_masculino";
        }
    }

    if (actor->id == ACTOR_EN_HY) {
        const int32_t type = actor->params & 0x7F;

        switch (type) {
            case 0:
            case 1:
            case 6:
            case 8:
            case 11:
            case 18:
                return "npc_feminino";
            default:
                return "npc_masculino";
        }
    }

    if (actor->id == ACTOR_EN_TG) {
        // En_Tg representa o casal inteiro. As reacoes a mascaras (0x711C-0x711F)
        // nao carregam um estado confiavel indicando qual integrante fala:
        // nextDialogue e inicializado a partir do frame e nem e alterado nesses
        // textos. Nao escolha genero aleatoriamente. Retornar nullptr faz o
        // player usar o WAV base/fallback deterministico.
        return nullptr;
    }

    return nullptr;
}

const char* ResolveFlatSharpSpeaker(Actor* actor) {
    if (actor == nullptr || actor->id != ACTOR_EN_POH) {
        actor = FindActorById(ACTOR_EN_POH);
    }

    if (actor == nullptr) {
        return nullptr;
    }

    const int32_t type = actor->params & 0xFF;
    if (type == EN_POH_SHARP) {
        return "sharp";
    }
    if (type == EN_POH_FLAT) {
        return "flat";
    }

    return nullptr;
}

const char* ResolveBowlingOrShootingSpeaker(Actor* actor) {
    if (actor != nullptr) {
        if (actor->id == ACTOR_EN_BOM_BOWL_MAN) {
            return "operadora_boliche_bombchu";
        }
        if (actor->id == ACTOR_EN_SYATEKI_MAN) {
            return "dono_tiro_ao_alvo";
        }
    }

    if (FindActorById(ACTOR_EN_BOM_BOWL_MAN) != nullptr) {
        return "operadora_boliche_bombchu";
    }
    if (FindActorById(ACTOR_EN_SYATEKI_MAN) != nullptr) {
        return "dono_tiro_ao_alvo";
    }

    return nullptr;
}

const char* ResolveShootingOrZoraSpeaker(Actor* actor) {
    if (actor != nullptr) {
        if (actor->id == ACTOR_EN_SYATEKI_MAN) {
            return "dono_tiro_ao_alvo";
        }
        if (actor->id == ACTOR_EN_DIVING_GAME) {
            return "npc_masculino";
        }
    }

    if (FindActorById(ACTOR_EN_DIVING_GAME) != nullptr) {
        return "npc_masculino";
    }
    if (FindActorById(ACTOR_EN_SYATEKI_MAN) != nullptr) {
        return "dono_tiro_ao_alvo";
    }

    return nullptr;
}

const char* ResolveDampeBowlingShopSpeaker(Actor* actor) {
    if (actor != nullptr) {
        if (actor->id == ACTOR_EN_TK) {
            return "dampe";
        }
        if (actor->id == ACTOR_EN_BOM_BOWL_MAN) {
            return "operadora_boliche_bombchu";
        }
        if (actor->id == ACTOR_EN_OSSAN) {
            return ResolveShopkeeperSpeaker(actor);
        }
    }

    if (FindActorById(ACTOR_EN_TK) != nullptr) {
        return "dampe";
    }
    if (FindActorById(ACTOR_EN_BOM_BOWL_MAN) != nullptr) {
        return "operadora_boliche_bombchu";
    }

    return ResolveShopkeeperSpeaker(nullptr);
}

const char* ResolveShopOrGrannySpeaker(Actor* actor) {
    if (actor != nullptr) {
        if (actor->id == ACTOR_EN_DS) {
            return "avo_pocoes";
        }
        if (actor->id == ACTOR_EN_OSSAN) {
            return ResolveShopkeeperSpeaker(actor);
        }
    }

    if (FindActorById(ACTOR_EN_DS) != nullptr) {
        return "avo_pocoes";
    }

    return ResolveShopkeeperSpeaker(nullptr);
}

const char* ResolveRuntimeSpeaker(uint16_t textId) {
    Actor* actor = ResolveActiveTalkActor(textId);

    switch (textId) {
        case 0x0217:
        case 0x0218:
        case 0x100F:
        case 0x1010:
        case 0x107C:
        case 0x7041:
        case 0x7043:
        case 0x7100:
        case 0x7101:
        case 0x7102:
        case 0x7103:
        case 0x710C:
        case 0x711A:
        case 0x711C:
        case 0x711D:
        case 0x711E:
        case 0x711F:
            return ResolveNpcGenderSpeaker(actor);

        case 0x5000:
        case 0x500F:
        case 0x5010:
        case 0x5011:
        case 0x5012:
        case 0x5013:
        case 0x5014:
            return ResolveFlatSharpSpeaker(actor);

        case 0x002D:
            return ResolveBowlingOrShootingSpeaker(actor);

        case 0x006A:
        case 0x006B:
        case 0x0086:
        case 0x009E:
            return ResolveShopkeeperSpeaker(actor);

        case 0x0085:
            return ResolveDampeBowlingShopSpeaker(actor);

        case 0x0096:
            return ResolveShopOrGrannySpeaker(actor);

        case 0x71AD:
            return ResolveShootingOrZoraSpeaker(actor);

        default:
            return nullptr;
    }
}

std::string BuildVoiceRelativePath(
    uint16_t textId,
    uint16_t page,
    const char* speakerVariant = nullptr
) {
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
        << page;

    if (speakerVariant != nullptr && speakerVariant[0] != '\0') {
        filename << "_" << speakerVariant;
    }

    filename << ".wav";
    return filename.str();
}

bool PlayVoiceFile(uint16_t textId, uint16_t page) {
    PTBRVoice_Stop();

    const char* speakerVariant = ResolveRuntimeSpeaker(textId);
    std::string relativePath =
        BuildVoiceRelativePath(textId, page, speakerVariant);
    std::string fullPath =
        Ship::Context::GetPathRelativeToAppDirectory(relativePath);

    if (speakerVariant != nullptr && !std::filesystem::exists(fullPath)) {
        SPDLOG_WARN(
            "[PTBR Voice] Variante '{}' ausente para textId=0x{:04X}, pagina={}; usando fallback base",
            speakerVariant,
            textId,
            page
        );

        relativePath = BuildVoiceRelativePath(textId, page);
        fullPath = Ship::Context::GetPathRelativeToAppDirectory(relativePath);
    }

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

    if (speakerVariant != nullptr) {
        SPDLOG_INFO(
            "[PTBR Voice] Tocando textId=0x{:04X}, pagina={}, falante={}: {}",
            textId,
            page,
            speakerVariant,
            relativePath
        );
    } else {
        SPDLOG_INFO(
            "[PTBR Voice] Tocando textId=0x{:04X}, pagina={}: {}",
            textId,
            page,
            relativePath
        );
    }

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
