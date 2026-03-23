import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class ApiService {
  static String get baseUrl {
    if (kIsWeb) {
      return 'https://visual-interaction-api.9622.online';
    }
    return 'http://127.0.0.1:5000';
  }

  static String get apiBaseUrl => baseUrl;

  static String getMediaUrl(String path) {
    if (path.startsWith('/media/')) {
      return '$baseUrl$path';
    }
    return path;
  }

  Future<Map<String, dynamic>> getSimulationData(
      Map<String, dynamic> params) async {
    try {
      print('Calling Sarvam TTS API...');
      final response = await http.post(
        Uri.parse('$baseUrl/api/simulation'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(params),
      );
      print('TTS completed: audio_url=present');
      return jsonDecode(response.body);
    } catch (e) {
      print('TTS failed: $e');
      return {'error': e.toString()};
    }
  }
}
