import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class SimulationModel extends ChangeNotifier {
  static const String baseUrl = 'http://172.20.199.176:5000';

  double _angle = 45.0;
  double _velocity = 20.0;
  double _gravity = 9.8;
  String _explanationText = '';
  String _speechAudioUrl = '';

  double get angle => _angle;
  double get velocity => _velocity;
  double get gravity => _gravity;
  String get explanationText => _explanationText;
  String get speechAudioUrl => _speechAudioUrl;

  Future<void> _fetchFromBackend() async {
    try {
      debugPrint(
          'Fetching from backend: angle=$_angle, velocity=$_velocity, gravity=$_gravity');

      final response = await http.post(
        Uri.parse('$baseUrl/api/simulate'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'angle': _angle,
          'velocity': _velocity,
          'gravity': _gravity,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _explanationText = data['explanation_text'] ?? '';
        _speechAudioUrl = data['speech_audio_url'] ?? '';
        debugPrint(
            'Response received: audio_url=${_speechAudioUrl.isNotEmpty ? "present" : "not present"}');
        notifyListeners();
      } else {
        debugPrint('Error: HTTP ${response.statusCode}');
      }
    } catch (e) {
      debugPrint('Error fetching from backend: $e');
    }
  }

  void setAngle(double value) {
    debugPrint('Slider changed: angle = $value');
    _angle = value;
    notifyListeners();
    _fetchFromBackend();
  }

  void setVelocity(double value) {
    debugPrint('Slider changed: velocity = $value');
    _velocity = value;
    notifyListeners();
    _fetchFromBackend();
  }

  void setGravity(double value) {
    debugPrint('Slider changed: gravity = $value');
    _gravity = value;
    notifyListeners();
    _fetchFromBackend();
  }

  double get maxRange {
    final angleRad = _angle * 3.14159 / 180;
    return (_velocity *
            _velocity *
            (2 * _angle.abs() > 180 ? -1 : 1) *
            (2 * _angle.abs() > 180 ? 0 : 1)) /
        _gravity;
  }

  double get maxHeight {
    final angleRad = _angle * 3.14159 / 180;
    return (_velocity * _velocity * (angleRad.abs() * angleRad.abs())) /
        (2 * _gravity);
  }
}
