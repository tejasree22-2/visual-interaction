import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../models/simulation_model.dart';

class Graph3D extends StatelessWidget {
  final SimulationModel model;

  const Graph3D({super.key, required this.model});

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: _Projectile3DPainter(model),
      size: Size.infinite,
    );
  }
}

class _Projectile3DPainter extends CustomPainter {
  final SimulationModel model;

  _Projectile3DPainter(this.model);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.blue
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    final axisPaint = Paint()
      ..color = Colors.grey
      ..strokeWidth = 1;

    final centerX = size.width / 2;
    final centerY = size.height / 2;

    canvas.drawLine(
      Offset(20, centerY),
      Offset(size.width - 20, centerY),
      axisPaint,
    );

    canvas.drawLine(
      Offset(centerX, size.height - 20),
      Offset(centerX, 20),
      axisPaint,
    );

    final path = Path();
    final angleRad = model.angle * math.pi / 180;
    final v = model.velocity;
    final g = model.gravity;

    final maxRange = (v * v * math.sin(2 * angleRad)) / g;
    const scale = 3.0;

    bool first = true;
    for (double t = 0; t <= 2 * v * math.sin(angleRad) / g; t += 0.02) {
      final x = v * math.cos(angleRad) * t;
      final y = v * math.sin(angleRad) * t - 0.5 * g * t * t;

      final screenX = centerX + x * scale;
      final screenY = size.height - 20 - y * scale;

      if (first) {
        path.moveTo(screenX, screenY);
        first = false;
      } else {
        path.lineTo(screenX, screenY);
      }
    }

    canvas.drawPath(path, paint);

    final textPainter = TextPainter(
      text: const TextSpan(
        text: '3D View (2D projection)',
        style: TextStyle(color: Colors.grey, fontSize: 14),
      ),
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(canvas, Offset(10, 10));
  }

  @override
  bool shouldRepaint(covariant _Projectile3DPainter oldDelegate) {
    return oldDelegate.model != model;
  }
}
