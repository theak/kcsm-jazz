#include <Arduino.h>
#include <Preferences.h>
#include "AudioTools.h"
#include "BluetoothA2DPSink.h"
#include "bluetooth.h"
#include "speaker.h"

// Routes received audio to the speaker, so voice prompts can cut in.
class SpeakerOutput : public BluetoothA2DPOutput {
 public:
  bool begin() override { return true; }
  size_t write(const uint8_t* data, size_t len) override { return speakerWrite(data, len); }
  void end() override {}
  void set_sample_rate(int rate) override { speakerSetSampleRate(rate); }
  void set_output_active(bool active) override {}
};

static SpeakerOutput output;
static BluetoothA2DPSink* a2dp = nullptr;  // only created in Bluetooth mode

static const char* slotKey(int slot) { return slot == 0 ? "slotA" : "slotB"; }

static bool loadSlot(int slot, uint8_t addr[ESP_BD_ADDR_LEN]) {
  Preferences prefs;
  prefs.begin("kcsm", true);
  bool found = prefs.getBytes(slotKey(slot), addr, ESP_BD_ADDR_LEN) == ESP_BD_ADDR_LEN;
  prefs.end();
  return found;
}

bool btSlotHasDevice(int slot) {
  uint8_t addr[ESP_BD_ADDR_LEN];
  return loadSlot(slot, addr);
}

void btStart(int slot, const char* name) {
  // The A2DP library reconnects to the address it stored as "last_bda". Point it
  // at this slot's device, or clear it so the box just waits to be paired.
  uint8_t addr[ESP_BD_ADDR_LEN];
  Preferences lib;
  lib.begin("connected_bda", false);
  if (loadSlot(slot, addr)) {
    lib.putBytes("last_bda", addr, ESP_BD_ADDR_LEN);
  } else {
    lib.remove("last_bda");
  }
  lib.end();

  a2dp = new BluetoothA2DPSink(output);
  a2dp->start(name, true);
}

bool btIsConnected() {
  return a2dp && a2dp->is_connected();
}

bool btIsPlaying() {
  return a2dp && a2dp->get_audio_state() == ESP_A2D_AUDIO_STATE_STARTED;
}

void btRememberDevice(int slot) {
  uint8_t* addr = *a2dp->get_current_peer_address();
  Serial.printf("Device %02x:%02x:%02x:%02x:%02x:%02x saved to slot %c\n",
                addr[0], addr[1], addr[2], addr[3], addr[4], addr[5], 'A' + slot);
  Preferences prefs;
  prefs.begin("kcsm", false);
  prefs.putBytes(slotKey(slot), addr, ESP_BD_ADDR_LEN);
  prefs.end();
}

void btDisconnect() {
  if (!btIsConnected()) return;
  a2dp->disconnect();
  delay(500);  // let the disconnect reach the device before we restart
}
