// widgets/bottom_subperiod_bar.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../services/bss_repository.dart';

class BottomSubperiodBar extends StatelessWidget {
  final List<SubPeriod> subPeriods;
  final int selectedSubPeriodId;
  final ValueChanged<int> onSubPeriodSelected;

  const BottomSubperiodBar({
    super.key,
    required this.subPeriods,
    required this.selectedSubPeriodId,
    required this.onSubPeriodSelected,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;
    final subTextColor = isDark ? BssColors.darkOakSubText : BssColors.subText;

    if (subPeriods.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      decoration: BoxDecoration(
        color: isDark ? BssColors.darkOakBg : BssColors.parchmentBg,
        border: Border(
          top: BorderSide(
            color: goldColor.withValues(alpha: 0.3),
            width: 1.0,
          ),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            height: 70,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: subPeriods.length,
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              itemBuilder: (context, index) {
                final sub = subPeriods[index];
                final isSelected = (sub.id == selectedSubPeriodId);

                return GestureDetector(
                  onTap: () => onSubPeriodSelected(sub.id),
                  child: Container(
                    width: 75,
                    margin: const EdgeInsets.symmetric(horizontal: 4.0),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // Timeline Node Indicator
                        Container(
                          width: 24,
                          height: 24,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: isSelected ? goldColor : Colors.transparent,
                            border: Border.all(
                              color: goldColor,
                              width: 1.5,
                            ),
                          ),
                          child: Center(
                            child: Text(
                              '${index + 1}',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: isSelected
                                    ? (isDark ? BssColors.darkOakBg : Colors.white)
                                    : textColor,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 4),
                        // Time Range Label
                        Text(
                          sub.timeRange,
                          style: TextStyle(
                            fontSize: 9,
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                            color: isSelected ? goldColor : subTextColor,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        // Title Label
                        Text(
                          sub.title,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 10,
                            color: textColor,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}