import 'package:flutter/material.dart';
import '../widgets/control_panel.dart';
import '../widgets/graph_2d.dart';
import '../widgets/graph_3d.dart';
import '../widgets/view_toggle.dart';
import '../widgets/audio_chunk_player.dart';
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
  bool _isPlaying = false;
  bool _showChunkPlayer = true;

  @override
  void initState() {
    super.initState();
    _speechService.setOnComplete(_onAudioComplete);
  }

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

  Future<void> _playExplanation() async {
    if (_isPlaying) {
      await _speechService.stop();
      setState(() {
        _isPlaying = false;
      });
    } else {
      final formula = _model.customFormula;
      await _speechService.speakWithFormula(
        angle: _model.angle,
        velocity: _model.velocity,
        gravity: _model.gravity,
        customFormula: formula,
        language: 'en-IN',
      );
      setState(() {
        _isPlaying = true;
      });
    }
  }

  void _onAudioComplete() {
    if (mounted) {
      setState(() {
        _isPlaying = false;
      });
    }
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
                  const SizedBox(height: 16),
                  AudioChunkPlayer(
                    angle: _model.angle,
                    velocity: _model.velocity,
                    gravity: _model.gravity,
                    customFormula: _model.customFormula,
                    language: 'en-IN',
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          setState(() {
            _showChunkPlayer = !_showChunkPlayer;
          });
        },
        icon: Icon(_showChunkPlayer ? Icons.expand_more : Icons.expand_less),
        label: Text(_showChunkPlayer ? 'Hide Lectures' : 'Show Lectures'),
        tooltip: _showChunkPlayer
            ? 'Hide lecture explanations'
            : 'Show lecture explanations',
      ),
    );
  }
}
