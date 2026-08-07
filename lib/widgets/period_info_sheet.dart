// widgets/period_info_sheet.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../models/lila_period.dart';
import 'lila_wheel.dart';

/// Bottom-sheet content shown from the clock icon: the 8-period wheel,
/// which period it is right now, and when the next one begins.
class PeriodInfoSheet extends StatelessWidget {
  final List<LilaPeriod> periods;
  final int currentPeriodId;
  final ValueChanged<int> onPeriodSelected;

  const PeriodInfoSheet({
    super.key,
    required this.periods,
    required this.currentPeriodId,
    required this.onPeriodSelected,
  });

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

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;
    final subTextCol = isDark ? BssColors.darkOakSubText : BssColors.subText;

    final currentIndex = periods.indexWhere((p) => p.id == currentPeriodId);
    final LilaPeriod? current = currentIndex >= 0 ? periods[currentIndex] : null;
    final LilaPeriod? next = periods.isNotEmpty
        ? periods[(currentIndex + 1) % periods.length]
        : null;

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
        countdown = h > 0 ? '${h}h ${m}m' : '${m}m';
      }
    }

    // Bottom sheets are only given a bounded height when the caller passes
    // isScrollControlled: true *and* the content is wrapped so it can
    // shrink/scroll instead of overflowing on shorter screens.
    final double maxSheetHeight = MediaQuery.of(context).size.height * 0.88;
    final double wheelSize = MediaQuery.of(context).size.width < 360 ? 220 : 240;

    return SafeArea(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxHeight: maxSheetHeight),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 36,
                height: 4,
                margin: const EdgeInsets.only(bottom: 14),
                decoration: BoxDecoration(
                  color: goldColor.withAlpha(140),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              // Shown up top too, so it's visible immediately even if the
              // rest of the sheet needs to scroll on a short screen.
              if (next != null)
                Text(
                  countdown != null
                      ? 'Next: ${next.title} in $countdown'
                      : 'Next: ${next.title}',
                  style: TextStyle(fontSize: 13, color: goldColor, fontWeight: FontWeight.w600),
                ),
              const SizedBox(height: 14),
              SizedBox(
                width: wheelSize,
                child: LilaWheelWidget(
                  periods: periods,
                  selectedPeriodId: currentPeriodId,
                  onPeriodSelected: (id) {
                    Navigator.of(context).pop();
                    onPeriodSelected(id);
                  },
                ),
              ),
              const SizedBox(height: 18),
              if (current != null) ...[
                Text(
                  'Current Period',
                  style: TextStyle(fontSize: 12, color: subTextCol),
                ),
                const SizedBox(height: 2),
                Text(
                  current.title,
                  style: TextStyle(
                    fontFamily: 'NotoSerif',
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: textColor,
                  ),
                ),
                Text(current.timeRange, style: TextStyle(color: subTextCol)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
