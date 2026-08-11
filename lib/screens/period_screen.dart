// screens/period_screen.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../models/danda.dart';
import '../models/lila_period.dart';
import '../services/bss_repository.dart';
import '../services/translations.dart';
import '../widgets/lila_wheel.dart';

/// Full-screen wheel of time (opened from the clock icon): the 8-period
/// wheel with the current period highlighted, which period it is right now
/// and when the next one begins, then a divider and the complete list of all
/// 60 ghatikās (24-minute divisions) with their short descriptions.
class PeriodScreen extends StatefulWidget {
  final BssRepository repository;
  final List<LilaPeriod> periods;
  final int currentPeriodId;
  final ValueChanged<int> onPeriodSelected;

  /// Name of the sub-period the clock is in right now (DB-driven).
  final String? currentSubPeriodTitle;

  /// 24-hour time range of that sub-period (e.g. "04:24 - 05:36").
  final String? currentSubPeriodTimeRange;

  const PeriodScreen({
    super.key,
    required this.repository,
    required this.periods,
    required this.currentPeriodId,
    required this.onPeriodSelected,
    this.currentSubPeriodTitle,
    this.currentSubPeriodTimeRange,
  });

  @override
  State<PeriodScreen> createState() => _PeriodScreenState();
}

class _PeriodScreenState extends State<PeriodScreen> {
  late Future<List<Danda>> _dandasFuture;

  @override
  void initState() {
    super.initState();
    _dandasFuture = widget.repository.getDandas();
  }

  /// Parses "HH:MM" into minutes-since-midnight.
  static int? _minutesOf(String hhmm) {
    final parts = hhmm.split(':');
    if (parts.length != 2) return null;
    final h = int.tryParse(parts[0]);
    final m = int.tryParse(parts[1]);
    if (h == null || m == null) return null;
    return h * 60 + m;
  }

  static (String, String)? _splitRange(String timeRange) {
    final parts = timeRange.split(' - ');
    if (parts.length != 2) return null;
    return (parts[0], parts[1]);
  }

  /// Current ghatikā number (1..60) derived from the clock time. The 24-hour
  /// day starts at the first main period's time_start (03:36); each ghatikā
  /// spans 24 minutes, so 60 ghatikās cover the whole day.
  int? _currentGhatika() {
    if (widget.periods.isEmpty) return null;
    final (String, String)? firstRange =
        _splitRange(widget.periods.first.timeRange);
    final int? dayStart = firstRange != null ? _minutesOf(firstRange.$1) : null;
    if (dayStart == null) return null;

    final DateTime now = DateTime.now();
    final int nowMinutes = now.hour * 60 + now.minute;
    final int elapsed = ((nowMinutes - dayStart) % (24 * 60) + 24 * 60) % (24 * 60);
    return elapsed ~/ 24 + 1;
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;
    final subTextCol = isDark ? BssColors.darkOakSubText : BssColors.subText;

    final currentIndex =
        widget.periods.indexWhere((p) => p.id == widget.currentPeriodId);
    final LilaPeriod? current =
        currentIndex >= 0 ? widget.periods[currentIndex] : null;
    final LilaPeriod? next = widget.periods.isNotEmpty
        ? widget.periods[(currentIndex + 1) % widget.periods.length]
        : null;
    final int? ghatika = _currentGhatika();

    String? countdown;
    if (next != null) {
      final range = _splitRange(next.timeRange);
      final startMinutes = range != null ? _minutesOf(range.$1) : null;
      if (startMinutes != null) {
        final now = DateTime.now();
        final nowMinutes = now.hour * 60 + now.minute;
        int diff = startMinutes - nowMinutes;
        if (diff <= 0) diff += 24 * 60;
        final h = diff ~/ 60;
        final m = diff % 60;
        countdown = h > 0
            ? Translations.t('period.info.countdown.hm')
                .replaceAll('{h}', '$h')
                .replaceAll('{m}', '$m')
            : Translations.t('period.info.countdown.m')
                .replaceAll('{m}', '$m');
      }
    }

    final double wheelSize =
        MediaQuery.of(context).size.width < 360 ? 240 : 280;

    return Scaffold(
      appBar: AppBar(title: Text(Translations.t('screen.periods.title'))),
      body: Column(
        children: [
          Expanded(
            child: SafeArea(
              top: false,
              child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
              children: [
                // Wheel
                Center(
                  child: SizedBox(
                    width: wheelSize,
                    child: LilaWheelWidget(
                      periods: widget.periods,
                      selectedPeriodId: widget.currentPeriodId,
                      onPeriodSelected: (id) {
                        Navigator.of(context).pop();
                        widget.onPeriodSelected(id);
                      },
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                // Current period info
                if (next != null)
                  Text(
                    countdown != null
                        ? Translations.t('period.info.nextIn')
                            .replaceAll('{title}', next.title)
                            .replaceAll('{countdown}', countdown)
                        : Translations.t('period.info.next')
                            .replaceAll('{title}', next.title),
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 13,
                      color: goldColor,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                const SizedBox(height: 10),
                if (current != null) ...[
                  Text(
                    Translations.t('period.info.current'),
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, color: subTextCol),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    current.title,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: textColor,
                    ),
                  ),
                  Text(
                    current.timeRange,
                    textAlign: TextAlign.center,
                    style: TextStyle(color: subTextCol),
                  ),
                  if (widget.currentSubPeriodTitle != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      Translations.t('period.info.currentSub'),
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 12, color: subTextCol),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      widget.currentSubPeriodTitle!,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        color: goldColor,
                      ),
                    ),
                    if (widget.currentSubPeriodTimeRange?.isNotEmpty ?? false) ...[
                      const SizedBox(height: 2),
                      Text(
                        widget.currentSubPeriodTimeRange!,
                        textAlign: TextAlign.center,
                        style: TextStyle(fontSize: 12, color: subTextCol),
                      ),
                    ],
                  ],
                  if (ghatika != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      Translations.t('period.ghatika.count')
                          .replaceAll('{count}', '$ghatika'),
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: goldColor,
                      ),
                    ),
                  ],
                ],
                const SizedBox(height: 16),
                const Divider(
                  height: 1,
                  thickness: 1,
                  color: Color(0x33D4AF37),
                ),
                const SizedBox(height: 12),
                // All 60 dandas, grouped by main period.
                FutureBuilder<List<Danda>>(
                  future: _dandasFuture,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Padding(
                        padding: EdgeInsets.symmetric(vertical: 32),
                        child: Center(child: CircularProgressIndicator()),
                      );
                    }
                    final dandas = snapshot.data ?? const <Danda>[];
                    if (dandas.isEmpty) {
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 24),
                        child: Text(
                          Translations.t('screen.periods.empty'),
                          textAlign: TextAlign.center,
                          style: TextStyle(color: subTextCol),
                        ),
                      );
                    }

                    final List<Widget> children = [];
                    for (final LilaPeriod period in widget.periods) {
                      final periodDandas = dandas
                          .where((d) => d.mainPeriodId == period.id)
                          .toList();
                      if (periodDandas.isEmpty) continue;

                      children.add(
                        Padding(
                          padding: const EdgeInsets.only(top: 14, bottom: 6),
                          child: Row(
                            children: [
                              Expanded(
                                child: Container(
                                  height: 1,
                                  color: goldColor.withAlpha(60),
                                ),
                              ),
                              Padding(
                                padding: const EdgeInsets.symmetric(horizontal: 10),
                                child: Text(
                                  period.title,
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.bold,
                                    color: goldColor,
                                  ),
                                ),
                              ),
                              Expanded(
                                child: Container(
                                  height: 1,
                                  color: goldColor.withAlpha(60),
                                ),
                              ),
                            ],
                          ),
                        ),
                      );

                      for (final Danda danda in periodDandas) {
                        children.add(
                          Padding(
                            padding: const EdgeInsets.only(bottom: 10),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                SizedBox(
                                  width: 34,
                                  child: Text(
                                    '${danda.id}',
                                    style: TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.bold,
                                      color: goldColor,
                                    ),
                                  ),
                                ),
                                SizedBox(
                                  width: 88,
                                  child: Text(
                                    danda.timeRange,
                                    style: TextStyle(
                                      fontSize: 11,
                                      color: subTextCol,
                                    ),
                                  ),
                                ),
                                Expanded(
                                  child: Text(
                                    danda.description,
                                    style: TextStyle(
                                      fontSize: 13,
                                      height: 1.35,
                                      color: textColor,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      }
                    }
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: children,
                    );
                  },
                ),
              ],
            ),
            ),
          ),
        ],
      ),
    );
  }
}
