import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class SpeechService {
  static const String baseUrl = 'http://172.20.199.176:5000';

  Future<void> speak(String text) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/simulate'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'text': text,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final audioUrl = data['speech_audio_url'];
        if (audioUrl != null) {
          // For now, just print - we can add audio playback later
          debugPrint('Audio URL received: $audioUrl');
        }
      }
    } catch (e) {
      debugPrint('Error calling backend: $e');
    }
  }

  Future<void> stop() async {}

  void dispose() {}
}
