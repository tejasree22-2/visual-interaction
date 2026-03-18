import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../models/simulation_model.dart';

class Graph2D extends StatefulWidget {
  final SimulationModel model;

  const Graph2D({super.key, required this.model});

  @override
  State<Graph2D> createState() => _Graph2DState();
}

class _Graph2DState extends State<Graph2D> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;
  bool _isPlaying = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    );
    _animation = Tween<double>(begin: 0, end: 1).animate(_controller)
      ..addListener(() => setState(() {}));
    _controller.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        setState(() => _isPlaying = false);
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _toggleAnimation() {
    if (_isPlaying) {
      _controller.stop();
    } else {
      if (_controller.status == AnimationStatus.completed) {
        _controller.reset();
      }
      _controller.forward();
    }
    setState(() => _isPlaying = !_isPlaying);
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        CustomPaint(
          painter: _ProjectilePainter(widget.model, _animation.value),
          size: Size.infinite,
        ),
        Positioned(
          right: 16,
          top: 16,
          child: FloatingActionButton(
            mini: true,
            onPressed: _toggleAnimation,
            child: Icon(_isPlaying ? Icons.pause : Icons.play_arrow),
          ),
        ),
      ],
    );
  }
}

class _ProjectilePainter extends CustomPainter {
  final SimulationModel model;
  final double animationValue;

  _ProjectilePainter(this.model, this.animationValue);

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
    final maxHeight =
        (v * v * math.sin(angleRad) * math.sin(angleRad)) / (2 * g);

    final flightTime = 2 * v * math.sin(angleRad) / g;

    const padding = 40.0;
    final scaleX = (size.width - padding) / maxRange;
    final scaleY = (size.height - padding) / maxHeight;

    bool first = true;
    for (double t = 0; t <= flightTime; t += 0.01) {
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

    final t = flightTime * animationValue;
    final ballX = v * math.cos(angleRad) * t;
    final ballY = v * math.sin(angleRad) * t - 0.5 * g * t * t;

    final ballScreenX = 20 + ballX * scaleX;
    final ballScreenY = size.height - 20 - ballY * scaleY;

    final ballPaint = Paint()
      ..color = Colors.red
      ..style = PaintingStyle.fill;
    canvas.drawCircle(Offset(ballScreenX, ballScreenY), 8, ballPaint);
  }

  @override
  bool shouldRepaint(covariant _ProjectilePainter oldDelegate) {
    return oldDelegate.model.angle != model.angle ||
        oldDelegate.model.velocity != model.velocity ||
        oldDelegate.model.gravity != model.gravity ||
        oldDelegate.animationValue != animationValue;
  }
}
