import 'package:flutter/material.dart';

// Safe fallback color constants matching your app design tokens
class _FallbackColors {
  static const Color darkOakBg = Color(0xFF1E1A16);
  static const Color darkOakCard = Color(0xFF2C2520);
  static const Color darkOakGold = Color(0xFFD4AF37);
  static const Color darkOakText = Color(0xFFE6D7C3);
  static const Color darkOakSubText = Color(0xFFA89985);
  
  static const Color parchmentBg = Color(0xFFF9F6F0);
  static const Color parchmentCard = Color(0xFFFFFFFF);
  static const Color goldAccent = Color(0xFFC5A059);
  static const Color darkText = Color(0xFF2C221E);
  static const Color subText = Color(0xFF7A6B63);
}

class PeriodWheel extends StatelessWidget {
  final List<dynamic> mainPeriods;
  final int selectedMainPeriodId;
  final ValueChanged<int> onMainPeriodSelected;

  const PeriodWheel({
    super.key,
    required this.mainPeriods,
    required this.selectedMainPeriodId,
    required this.onMainPeriodSelected,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? _FallbackColors.darkOakGold : _FallbackColors.goldAccent;
    final textColor = isDark ? _FallbackColors.darkOakText : _FallbackColors.darkText;
    final activeBg = isDark ? _FallbackColors.darkOakCard : _FallbackColors.parchmentCard;

    if (mainPeriods.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      height: 48,
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      decoration: BoxDecoration(
        color: isDark ? _FallbackColors.darkOakBg : _FallbackColors.parchmentBg,
        border: Border(
          bottom: BorderSide(
            color: goldColor.withAlpha(76),
            width: 1.0,
          ),
        ),
      ),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: mainPeriods.length,
        padding: const EdgeInsets.symmetric(horizontal: 8.0),
        itemBuilder: (context, index) {
          final period = mainPeriods[index];
          final int periodId = (period is Map) ? (period['id'] ?? index + 1) : (period.id ?? index + 1);
          final String periodTitle = (period is Map) ? (period['title'] ?? 'Period ${index + 1}') : (period.title.isNotEmpty ? period.title : 'Period ${index + 1}');
          final isSelected = (periodId == selectedMainPeriodId);

          return GestureDetector(
            onTap: () => onMainPeriodSelected(periodId),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 4.0),
              margin: const EdgeInsets.symmetric(horizontal: 4.0),
              decoration: BoxDecoration(
                color: isSelected ? goldColor : activeBg,
                borderRadius: BorderRadius.circular(8.0),
                border: Border.all(
                  color: goldColor,
                  width: 1.0,
                ),
              ),
              child: Center(
                child: Text(
                  periodTitle,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: isSelected
                        ? (isDark ? _FallbackColors.darkOakBg : Colors.white)
                        : textColor,
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}