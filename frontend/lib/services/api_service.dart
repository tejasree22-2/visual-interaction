import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class ApiService {
  static String get baseUrl {
    if (kIsWeb) {
      return 'http://localhost:5000';
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

  Future<List<List<double>>> calculateTrajectory({
    required double angle,
    required double velocity,
    required double gravity,
  }) async {
    final result = await getSimulationData({
      'angle': angle,
      'velocity': velocity,
      'gravity': gravity,
    });
    final trajectoryData = result['trajectory'];
    if (trajectoryData == null) return [];
    return (trajectoryData as List<dynamic>)
        .map((e) => [(e[0] as num).toDouble(), (e[1] as num).toDouble()])
        .toList();
  }
}
