import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../services/bss_repository.dart';

class RightNumberRail extends StatelessWidget {
  final List<LilaSectionItem> sections;
  final int selectedSectionId;
  final ValueChanged<int> onSectionSelected;

  const RightNumberRail({
    super.key,
    required this.sections,
    required this.selectedSectionId,
    required this.onSectionSelected,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;

    if (sections.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      width: 50,
      margin: const EdgeInsets.symmetric(vertical: 4.0),
      padding: const EdgeInsets.symmetric(vertical: 6.0, horizontal: 2.0),
      decoration: BoxDecoration(
        color: (isDark ? BssColors.darkOakCard : BssColors.parchmentCard).withAlpha(235),
        borderRadius: BorderRadius.zero,
        border: Border(
          left: BorderSide(color: goldColor.withAlpha(102), width: 1.0),
          top: BorderSide(color: goldColor.withAlpha(102), width: 1.0),
          bottom: BorderSide(color: goldColor.withAlpha(102), width: 1.0),
        ),
      ),
      child: Column(
        children: [
          Text(
            '${sections.length}',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: goldColor,
            ),
          ),
          Text(
            'Līlās',
            style: TextStyle(
              fontSize: 8,
              color: isDark ? BssColors.darkOakSubText : BssColors.subText,
            ),
          ),
          const SizedBox(height: 4),
          const Divider(height: 1),
          const SizedBox(height: 4),

          Expanded(
            child: ListView.builder(
              itemCount: sections.length,
              padding: EdgeInsets.zero,
              itemBuilder: (context, index) {
                final section = sections[index];
                final isSelected = (section.id == selectedSectionId);

                return GestureDetector(
                  onTap: () => onSectionSelected(section.id),
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 3.0),
                    alignment: Alignment.center,
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 180),
                      width: 28,
                      height: 28,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: isSelected ? goldColor : Colors.transparent,
                        border: Border.all(
                          color: goldColor,
                          width: 1.2,
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