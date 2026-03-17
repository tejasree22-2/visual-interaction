import 'package:flutter/material.dart';
import '../models/simulation_model.dart';

class ControlPanel extends StatelessWidget {
  final SimulationModel model;

  const ControlPanel({super.key, required this.model});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Controls',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            _buildSlider(
              context,
              'Angle',
              model.angle,
              0,
              90,
              (value) => model.setAngle(value),
              '${model.angle.toStringAsFixed(1)}°',
            ),
            _buildSlider(
              context,
              'Velocity',
              model.velocity,
              0,
              100,
              (value) => model.setVelocity(value),
              '${model.velocity.toStringAsFixed(1)} m/s',
            ),
            _buildSlider(
              context,
              'Gravity',
              model.gravity,
              1,
              20,
              (value) => model.setGravity(value),
              '${model.gravity.toStringAsFixed(1)} m/s²',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSlider(
    BuildContext context,
    String label,
    double value,
    double min,
    double max,
    ValueChanged<double> onChanged,
    String displayValue,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label),
            Text(displayValue),
          ],
        ),
        Slider(
          value: value,
          min: min,
          max: max,
          onChanged: onChanged,
        ),
      ],
    );
  }
}
