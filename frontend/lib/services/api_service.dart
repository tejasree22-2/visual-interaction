import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class ApiService {
  static String get baseUrl {
    if (kIsWeb) {
      return 'https://visual-interaction-api.9622.online';
    }
    return 'http://10.0.2.2:5000';
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
      final response = await http.post(
        Uri.parse('$baseUrl/api/simulation'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(params),
      );
      return jsonDecode(response.body);
    } catch (e) {
      return {'error': e.toString()};
    }
  }
}
