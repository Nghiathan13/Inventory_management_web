// // //---------------------------------------------------------------// // //
// // ---------------- LIBRARIES ----------------- // // //
#include <Arduino.h>



// // //---------------------------------------------------------------// // //
// // ---------------- SETUP ----------------- // // //
void setup() {
  Serial.begin(115200);
  Serial.println("San sang nhan lenh...");
}

// // //---------------------------------------------------------------// // //
// // ---------------- MAIN FUNCTION ----------------- // // //
void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command.equalsIgnoreCase("HOMING")) {
      delay(10000);
      Serial.println("DONE:2");
    }
    else {
      int first_colon = command.indexOf(':');
      int second_colon = command.indexOf(':', first_colon + 1);

      if (first_colon == -1 || second_colon == -1) {
        Serial.println("Syntax error");
        return;
      }
      else {
        String param1_str = command.substring(first_colon + 1, second_colon);
        String param2_str = command.substring(second_colon + 1);

        int target_shelf = param1_str.toInt();
        int target_tray = param2_str.toInt();

        if (command.startsWith("FETCH:"))
        {
          delay(5000);
          Serial.print("DONE:");
          Serial.println(target_shelf);
        }
        else if (command.startsWith("STORE:"))
        {
          delay(2000);
          Serial.print("DONE:");
          Serial.println(target_shelf);
        }
      }
    }

  }
}
