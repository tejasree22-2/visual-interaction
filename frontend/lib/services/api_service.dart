import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://172.20.199.176:5000';

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

  Future<List<double>> calculateTrajectory({
    required double angle,
    required double velocity,
    required double gravity,
  }) async {
    final result = await getSimulationData({
      'angle': angle,
      'velocity': velocity,
      'gravity': gravity,
    });
    return List<double>.from(result['trajectory'] ?? []);
  }
}
