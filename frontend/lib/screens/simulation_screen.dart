import 'package:flutter/material.dart';
import '../widgets/control_panel.dart';
import '../widgets/graph_2d.dart';
import '../widgets/graph_3d.dart';
import '../widgets/view_toggle.dart';
import '../widgets/formula_editor.dart';
import '../services/speech_service.dart';
import '../models/simulation_model.dart';

class SimulationScreen extends StatefulWidget {
  const SimulationScreen({super.key});

  @override
  State<SimulationScreen> createState() => _SimulationScreenState();
}

class _SimulationScreenState extends State<SimulationScreen> {
  final SimulationModel _model = SimulationModel();
  final SpeechService _speechService = SpeechService();
  bool _is3DView = false;

  @override
  void dispose() {
    _speechService.dispose();
    super.dispose();
  }

  void _toggleView(bool is3D) {
    setState(() {
      _is3DView = is3D;
    });
  }

  void _playExplanation() {
    final angle = _model.angle.toStringAsFixed(1);
    final velocity = _model.velocity.toStringAsFixed(1);
    final gravity = _model.gravity.toStringAsFixed(1);
    final formula = _model.customFormula;

    _speechService.speakWithFormula(
      angle: _model.angle,
      velocity: _model.velocity,
      gravity: _model.gravity,
      customFormula: formula,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Projectile Simulation'),
        actions: [
          IconButton(
            icon: const Icon(Icons.volume_up),
            onPressed: _playExplanation,
            tooltip: 'Play audio explanation',
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            flex: 3,
            child: _is3DView ? Graph3D(model: _model) : Graph2D(model: _model),
          ),
          Expanded(
            flex: 2,
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  ViewToggle(onToggle: _toggleView, value: _is3DView),
                  const SizedBox(height: 16),
                  ControlPanel(model: _model),
                ],
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _playExplanation,
        icon: const Icon(Icons.volume_up),
        label: const Text('Text to Speech'),
        tooltip: 'Play audio explanation',
      ),
    );
  }
}
