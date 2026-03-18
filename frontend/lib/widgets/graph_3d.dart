import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../models/simulation_model.dart';

class Graph3D extends StatefulWidget {
  final SimulationModel model;

  const Graph3D({super.key, required this.model});

  @override
  State<Graph3D> createState() => _Graph3DState();
}

class _Graph3DState extends State<Graph3D> with SingleTickerProviderStateMixin {
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
        ListenableBuilder(
          listenable: widget.model,
          builder: (context, _) => CustomPaint(
            painter: _Projectile3DPainter(widget.model, _animation.value),
            size: Size.infinite,
          ),
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

class _Projectile3DPainter extends CustomPainter {
  final SimulationModel model;
  final double animationValue;

  _Projectile3DPainter(this.model, this.animationValue);

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

    final flightTime = 2 * v * math.sin(angleRad) / g;
    const scale = 3.0;

    bool first = true;
    for (double t = 0; t <= flightTime; t += 0.02) {
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

    final t = flightTime * animationValue;
    final ballX = v * math.cos(angleRad) * t;
    final ballY = v * math.sin(angleRad) * t - 0.5 * g * t * t;

    final ballScreenX = centerX + ballX * scale;
    final ballScreenY = size.height - 20 - ballY * scale;

    final ballPaint = Paint()
      ..color = Colors.red
      ..style = PaintingStyle.fill;
    canvas.drawCircle(Offset(ballScreenX, ballScreenY), 8, ballPaint);

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
    return oldDelegate.model.angle != model.angle ||
        oldDelegate.model.velocity != model.velocity ||
        oldDelegate.model.gravity != model.gravity ||
        oldDelegate.animationValue != animationValue;
  }
}
