import 'package:flutter/foundation.dart';

class SimulationModel extends ChangeNotifier {
  double _angle = 45.0;
  double _velocity = 20.0;
  double _gravity = 9.8;

  double get angle => _angle;
  double get velocity => _velocity;
  double get gravity => _gravity;

  void setAngle(double value) {
    _angle = value;
    notifyListeners();
  }

  void setVelocity(double value) {
    _velocity = value;
    notifyListeners();
  }

  void setGravity(double value) {
    _gravity = value;
    notifyListeners();
  }

  double get maxRange {
    final angleRad = _angle * 3.14159 / 180;
    return (_velocity * _velocity * (2 * _angle.abs() > 180 ? -1 : 1) * 
            (2 * _angle.abs() > 180 ? 0 : 1)) /
        _gravity;
  }

  double get maxHeight {
    final angleRad = _angle * 3.14159 / 180;
    return (_velocity * _velocity * 
            (angleRad.abs() * angleRad.abs())) /
        (2 * _gravity);
  }
}
