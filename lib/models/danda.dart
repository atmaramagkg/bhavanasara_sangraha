// models/danda.dart
/// One 24-minute ghatikā of the day. There are 60 of them, grouped under the
/// 8 main periods (see `LilaPeriod`). Descriptions come from the `dandas`
/// table joined to `translations` by `description_key`.
class Danda {
  final int id;
  final int mainPeriodId;
  final int sortOrder;
  final String timeStart;
  final String timeEnd;
  final String description;

  const Danda({
    required this.id,
    required this.mainPeriodId,
    required this.sortOrder,
    required this.timeStart,
    required this.timeEnd,
    required this.description,
  });

  String get timeRange =>
      timeStart.isNotEmpty && timeEnd.isNotEmpty ? '$timeStart - $timeEnd' : '';
}
