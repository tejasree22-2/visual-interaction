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
      text: widget.model.customFormula,
    );
  }

  @override
  void dispose() {
    _formulaController.dispose();
    super.dispose();
  }

  void _onFormulaChanged(String value) {
    widget.model.setCustomFormula(value);
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
              onChanged: _onFormulaChanged,
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
