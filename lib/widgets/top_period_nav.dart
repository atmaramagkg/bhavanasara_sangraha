import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../models/lila_period.dart';
import '../services/bss_repository.dart';

class TopPeriodNav extends StatelessWidget {
  final List<LilaPeriod> mainPeriods;
  final int selectedMainPeriodId;
  final ValueChanged<int> onMainPeriodSelected;

  final List<SubPeriod> subPeriods;
  final int selectedSubPeriodId;
  final ValueChanged<int> onSubPeriodSelected;

  const TopPeriodNav({
    super.key,
    required this.mainPeriods,
    required this.selectedMainPeriodId,
    required this.onMainPeriodSelected,
    required this.subPeriods,
    required this.selectedSubPeriodId,
    required this.onSubPeriodSelected,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;
    final activeBg = isDark ? BssColors.darkOakCard : BssColors.parchmentCard;

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      decoration: BoxDecoration(
        color: isDark ? BssColors.darkOakBg : BssColors.parchmentBg,
        border: Border(
          bottom: BorderSide(
            color: goldColor.withAlpha(76),
            width: 1.0,
          ),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            height: 36,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: mainPeriods.length,
              padding: const EdgeInsets.symmetric(horizontal: 8.0),
              itemBuilder: (context, index) {
                final period = mainPeriods[index];
                final isSelected = (period.id == selectedMainPeriodId);

                return GestureDetector(
                  onTap: () => onMainPeriodSelected(period.id),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 180),
                    width: 38,
                    margin: const EdgeInsets.symmetric(horizontal: 2.0),
                    decoration: BoxDecoration(
                      color: isSelected ? goldColor : activeBg,
                      borderRadius: BorderRadius.circular(6.0),
                      border: Border.all(
                        color: goldColor,
                        width: 1.0,
                      ),
                    ),
                    child: Center(
                      child: Text(
                        '${index + 1}',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: isSelected
                              ? (isDark ? BssColors.darkOakBg : Colors.white)
                              : textColor,
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),

          if (subPeriods.isNotEmpty) ...[
            const SizedBox(height: 6),
            SizedBox(
              height: 28,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: subPeriods.length,
                padding: const EdgeInsets.symmetric(horizontal: 8.0),
                itemBuilder: (context, index) {
                  final sub = subPeriods[index];
                  final isSelected = (sub.id == selectedSubPeriodId);

                  return GestureDetector(
                    onTap: () => onSubPeriodSelected(sub.id),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 180),
                      padding: const EdgeInsets.symmetric(horizontal: 10.0, vertical: 4.0),
                      margin: const EdgeInsets.symmetric(horizontal: 3.0),
                      decoration: BoxDecoration(
                        color: isSelected ? goldColor.withAlpha(64) : Colors.transparent,
                        borderRadius: BorderRadius.circular(14.0),
                        border: Border.all(
                          color: isSelected ? goldColor : goldColor.withAlpha(76),
                          width: 1.0,
                        ),
                      ),
                      child: Center(
                        child: Text(
                          sub.timeRange,
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                            color: isSelected ? goldColor : textColor,
                          ),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ],
      ),
    );
  }
}