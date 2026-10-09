#include <Arduino.h>
#include "AudioTools.h"
#include "board.h"
#include "speaker.h"

static const float PROMPT_GAIN = 0.6f;    // prompts are normalized loud; keep them below the music
static const int PROMPT_GAP_MS = 150;     // silence after each prompt

static I2SStream i2s;
static int sampleRate = 44100;
static volatile bool speaking = false;

void speakerBegin() {
  auto cfg = i2s.defaultConfig(TX_MODE);
  cfg.pin_bck = I2S_BCLK;
  cfg.pin_ws = I2S_LRC;
  cfg.pin_data = I2S_DOUT;
  cfg.pin_mck = I2S_MCLK;
  cfg.sample_rate = sampleRate;
  cfg.channels = 2;
  cfg.bits_per_sample = 16;
  i2s.begin(cfg);
}

void speakerEnd() {
  i2s.end();
}

void speakerSetSampleRate(int rate) {
  if (rate == sampleRate) return;
  sampleRate = rate;
  i2s.setAudioInfo(AudioInfo(rate, 2, 16));
}

size_t speakerWrite(const uint8_t* data, size_t len) {
  if (speaking) return len;
  return i2s.write(data, len);
}

// G.711 mu-law to 16-bit linear
static int16_t ulawDecode(uint8_t u) {
  u = ~u;
  int t = ((u & 0x0F) << 3) + 0x84;
  t <<= (u & 0x70) >> 4;
  return (u & 0x80) ? (0x84 - t) : (t - 0x84);
}

void say(PromptId id) {
  const Prompt& p = PROMPTS[id];
  speaking = true;

  // Step through the 16 kHz clip at the output rate (16.16 fixed point),
  // interpolating between samples, and write it to both channels. pos is 64-bit
  // because a 32-bit 16.16 position wraps after 65536 samples (4.1 s of prompt).
  int16_t frames[256][2];
  int n = 0;
  const uint64_t step = ((uint64_t)PROMPT_SAMPLE_RATE << 16) / sampleRate;
  for (uint64_t pos = 0; (pos >> 16) + 1 < p.len; pos += step) {
    uint32_t i = pos >> 16;
    int32_t a = ulawDecode(p.data[i]);
    int32_t b = ulawDecode(p.data[i + 1]);
    int32_t s = a + (int32_t)(((int64_t)(b - a) * (pos & 0xFFFF)) >> 16);
    frames[n][0] = frames[n][1] = (int16_t)(s * PROMPT_GAIN);
    if (++n == 256) {
      i2s.write((uint8_t*)frames, sizeof(frames));
      n = 0;
    }
  }
  if (n) i2s.write((uint8_t*)frames, n * sizeof(frames[0]));

  memset(frames, 0, sizeof(frames));
  for (int left = sampleRate * PROMPT_GAP_MS / 1000; left > 0; left -= 256) {
    i2s.write((uint8_t*)frames, min(left, 256) * sizeof(frames[0]));
  }
  speaking = false;
}
