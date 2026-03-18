import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:math' as math;
import '../services/api_service.dart';

class SimulationModel extends ChangeNotifier {
  static String get baseUrl => ApiService.apiBaseUrl;

  double _angle = 45.0;
  double _velocity = 20.0;
  double _gravity = 9.8;
  String _customFormula = 'y = x * tan(θ) - (g * x²) / (2 * v² * cos²(θ))';
  String _explanationText = '';
  String _speechAudioUrl = '';
  List<List<double>> _trajectory = [];
  double _maxHeight = 0;
  double _range = 0;
  double _timeOfFlight = 0;

  SimulationModel() {
    _updateFormula();
    _fetchFromBackend();
  }

  double get angle => _angle;
  double get velocity => _velocity;
  double get gravity => _gravity;
  String get customFormula => _customFormula;
  String get explanationText => _explanationText;
  String get speechAudioUrl => _speechAudioUrl;
  List<List<double>> get trajectory => _trajectory;
  double get maxHeightBackend => _maxHeight;
  double get range => _range;
  double get timeOfFlight => _timeOfFlight;

  void _calculateTrajectoryLocally() {
    final angleRad = _angle * math.pi / 180;
    final vx = _velocity * math.cos(angleRad);
    final vy = _velocity * math.sin(angleRad);

    _timeOfFlight = 2 * vy / _gravity;
    _maxHeight = (vy * vy) / (2 * _gravity);
    _range = _velocity * _velocity * math.sin(2 * angleRad) / _gravity;

    _trajectory = [];
    const numPoints = 100;
    for (int i = 0; i <= numPoints; i++) {
      final t = (i / numPoints) * _timeOfFlight;
      final x = vx * t;
      final y = vy * t - 0.5 * _gravity * t * t;
      _trajectory.add([x, y < 0 ? 0 : y]);
    }
    notifyListeners();
  }

  Future<void> _fetchFromBackend() async {
    try {
      debugPrint(
          'Fetching from backend: angle=$_angle, velocity=$_velocity, gravity=$_gravity, formula=$_customFormula');

      final response = await http.post(
        Uri.parse('$baseUrl/api/simulate'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'angle': _angle,
          'velocity': _velocity,
          'gravity': _gravity,
          'custom_formula': _customFormula,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _explanationText = data['explanation_text'] ?? '';
        _speechAudioUrl = data['speech_audio_url'] ?? '';
        _trajectory = (data['trajectory'] as List<dynamic>?)
                ?.map(
                    (e) => [(e[0] as num).toDouble(), (e[1] as num).toDouble()])
                .toList() ??
            [];
        _maxHeight = (data['max_height'] as num?)?.toDouble() ?? 0;
        _range = (data['range'] as num?)?.toDouble() ?? 0;
        _timeOfFlight = (data['time_of_flight'] as num?)?.toDouble() ?? 0;

        if (_trajectory.isEmpty) {
          debugPrint(
              'Backend returned empty trajectory, using local calculation');
          _calculateTrajectoryLocally();
        } else {
          debugPrint(
              'Response received: audio_url=${_speechAudioUrl.isNotEmpty ? "present" : "not present"}, trajectory_points=${_trajectory.length}');
          notifyListeners();
        }
      } else {
        debugPrint(
            'Error: HTTP ${response.statusCode}, using local calculation');
        _calculateTrajectoryLocally();
      }
    } catch (e) {
      debugPrint('Error fetching from backend: $e, using local calculation');
      _calculateTrajectoryLocally();
    }
  }

  void setAngle(double value) {
    debugPrint('Slider changed: angle = $value');
    _angle = value;
    _updateFormula();
    notifyListeners();
    _fetchFromBackend();
  }

  void setVelocity(double value) {
    debugPrint('Slider changed: velocity = $value');
    _velocity = value;
    _updateFormula();
    notifyListeners();
    _fetchFromBackend();
  }

  void setGravity(double value) {
    debugPrint('Slider changed: gravity = $value');
    _gravity = value;
    _updateFormula();
    notifyListeners();
    _fetchFromBackend();
  }

  void _updateFormula() {
    _customFormula =
        'y = x * tan(${_angle.toStringAsFixed(1)}°) - (${_gravity.toStringAsFixed(1)} * x²) / (2 * ${_velocity.toStringAsFixed(1)}² * cos²(${_angle.toStringAsFixed(1)}°))';
  }

  void setCustomFormula(String formula) {
    debugPrint('Custom formula changed: $formula');
    _customFormula = formula;
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
