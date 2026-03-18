import 'package:flutter/material.dart';

class ViewToggle extends StatelessWidget {
  final Function(bool) onToggle;
  final bool value;

  const ViewToggle({
    super.key,
    required this.onToggle,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('2D'),
            const SizedBox(width: 8),
            Switch(
              value: value,
              onChanged: (value) => onToggle(value),
            ),
            const SizedBox(width: 8),
            const Text('3D'),
          ],
        ),
      ),
    );
  }
}
