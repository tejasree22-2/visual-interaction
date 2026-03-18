import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:math' as math;
import 'package:audioplayers/audioplayers.dart';
import 'api_service.dart';

class SpeechService {
  static String get baseUrl => ApiService.apiBaseUrl;
  final AudioPlayer _audioPlayer = AudioPlayer();
  final FlutterTts _flutterTts = FlutterTts();
  bool _useBackendTts = true;
  Function? _onComplete;

  SpeechService() {
    _initTts();
    _initAudioPlayer();
  }

  void _initAudioPlayer() {
    _audioPlayer.setPlayerMode(PlayerMode.lowLatency);
    _audioPlayer.setReleaseMode(ReleaseMode.stop);
    _audioPlayer.onPlayerComplete.listen((_) {
      _onComplete?.call();
    });
  }

  Future<void> _initTts() async {
    await _flutterTts.setLanguage("te-IN");
    await _flutterTts.setSpeechRate(0.5);
    await _flutterTts.setVolume(1.0);
    await _flutterTts.setPitch(1.0);
  }

  void setOnComplete(Function callback) {
    _onComplete = callback;
  }

  Future<void> speakWithFormula({
    required double angle,
    required double velocity,
    required double gravity,
    required String customFormula,
    String language = 'te-IN',
  }) async {
    if (_useBackendTts) {
      try {
        final response = await http
            .post(
              Uri.parse('$baseUrl/api/simulate'),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({
                'text': '',
                'angle': angle,
                'velocity': velocity,
                'gravity': gravity,
                'custom_formula': customFormula,
                'include_formula': true,
                'language': language,
              }),
            )
            .timeout(const Duration(seconds: 15));

        if (response.statusCode == 200) {
          final data = jsonDecode(response.body);
          final audioUrl = data['speech_audio_url'];
          if (audioUrl != null && audioUrl.isNotEmpty) {
            await _audioPlayer.stop();
            await _audioPlayer.setSourceUrl(ApiService.getMediaUrl(audioUrl));
            await _audioPlayer.resume();
            return;
          }
        }
      } catch (e) {
        debugPrint('Backend TTS failed: $e');
      }
    }

    final formulaText = _convertFormulaToSpeech(customFormula);
    final explanation = 'Formula: $formulaText. '
        'Ipudu i simulation lo, projectile $angle degrees angle daari, '
        '$velocity m/s velocity tho launch avutundi. '
        'Maximum height: ${(velocity * velocity * math.sin(angle * math.pi / 180) * math.sin(angle * math.pi / 180)) / (2 * gravity)}. '
        'Range: ${(velocity * velocity * math.sin(2 * angle * math.pi / 180)) / gravity}.';

    debugPrint('Using fallback TTS with formula');
    await _flutterTts.speak(explanation);
  }

  String _convertFormulaToSpeech(String formula) {
    return formula
        .replaceAll('θ', 'theta')
        .replaceAll('²', ' squared ')
        .replaceAll('³', ' cubed ')
        .replaceAll('*', ' multiplied by ')
        .replaceAll('/', ' divided by ')
        .replaceAll('+', ' plus ')
        .replaceAll('-', ' minus ')
        .replaceAll('=', ' equals ')
        .replaceAll('(', ' open parenthesis ')
        .replaceAll(')', ' close parenthesis ')
        .replaceAll('x ', ' x ')
        .replaceAll(' v ', ' v ')
        .replaceAll(' g ', ' g ')
        .replaceAll(' tan ', ' tangent ')
        .replaceAll(' cos ', ' cosine ')
        .replaceAll(' sin ', ' sine ');
  }

  Future<void> speak(String text) async {
    if (_useBackendTts) {
      try {
        final response = await http
            .post(
              Uri.parse('$baseUrl/api/simulate'),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({
                'text': text,
              }),
            )
            .timeout(const Duration(seconds: 15));

        if (response.statusCode == 200) {
          final data = jsonDecode(response.body);
          final audioUrl = data['speech_audio_url'];
          if (audioUrl != null && audioUrl.isNotEmpty) {
            await _audioPlayer.stop();
            await _audioPlayer.setSourceUrl(ApiService.getMediaUrl(audioUrl));
            await _audioPlayer.resume();
            return;
          }
        }
      } catch (e) {
        debugPrint('Backend TTS failed: $e');
      }
    }

    debugPrint('Using fallback TTS');
    await _flutterTts.speak(text);
  }

  Future<void> stop() async {
    await _audioPlayer.stop();
    await _flutterTts.stop();
  }

  void dispose() {
    _audioPlayer.dispose();
    _flutterTts.stop();
  }
}
