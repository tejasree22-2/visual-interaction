import 'package:flutter/material.dart';
import '../models/simulation_model.dart';

class FormulaEditor extends StatefulWidget {
  final SimulationModel model;

  const FormulaEditor({super.key, required this.model});

  @override
  State<FormulaEditor> createState() => _FormulaEditorState();
}

class _FormulaEditorState extends State<FormulaEditor> {
  late TextEditingController _formulaController;

  @override
  void initState() {
    super.initState();
    _formulaController = TextEditingController(
      text: 'y = x * tan(θ) - (g * x²) / (2 * v² * cos²(θ))',
    );
  }

  @override
  void dispose() {
    _formulaController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Formula Editor',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _formulaController,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: 'Enter custom formula',
              ),
            ),
          ],
        ),
      ),
    );
  }
}
