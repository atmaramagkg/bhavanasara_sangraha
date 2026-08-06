// models/lila_period.dart
class LilaPeriod {
  final int id;
  final String code;
  final String nameKey;
  final String title;     // Loaded from translations table
  final String timeRange; // Built from time_start and time_end

  const LilaPeriod({
    required this.id,
    required this.code,
    required this.nameKey,
    required this.title,
    required this.timeRange,
  });
}