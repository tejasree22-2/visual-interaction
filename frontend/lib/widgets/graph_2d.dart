import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../models/simulation_model.dart';

class Graph2D extends StatelessWidget {
  final SimulationModel model;

  const Graph2D({super.key, required this.model});

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: _ProjectilePainter(model),
      size: Size.infinite,
    );
  }
}

class _ProjectilePainter extends CustomPainter {
  final SimulationModel model;

  _ProjectilePainter(this.model);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.blue
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    final axisPaint = Paint()
      ..color = Colors.grey
      ..strokeWidth = 1;

    canvas.drawLine(
      Offset(0, size.height - 20),
      Offset(size.width, size.height - 20),
      axisPaint,
    );

    canvas.drawLine(
      Offset(20, 0),
      Offset(20, size.height),
      axisPaint,
    );

    final path = Path();
    final angleRad = model.angle * math.pi / 180;
    final v = model.velocity;
    final g = model.gravity;

    final maxRange = (v * v * math.sin(2 * angleRad)) / g;
    final maxHeight = (v * v * math.sin(angleRad) * math.sin(angleRad)) / (2 * g);

    const padding = 40.0;
    final scaleX = (size.width - padding) / maxRange;
    final scaleY = (size.height - padding) / maxHeight;

    bool first = true;
    for (double t = 0; t <= 2 * v * math.sin(angleRad) / g; t += 0.01) {
      final x = v * math.cos(angleRad) * t;
      final y = v * math.sin(angleRad) * t - 0.5 * g * t * t;

      final screenX = 20 + x * scaleX;
      final screenY = size.height - 20 - y * scaleY;

      if (first) {
        path.moveTo(screenX, screenY);
        first = false;
      } else {
        path.lineTo(screenX, screenY);
      }
    }

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant _ProjectilePainter oldDelegate) {
    return oldDelegate.model != model;
  }
}
