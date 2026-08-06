// widgets/lila_wheel.dart
import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../models/lila_period.dart';

class LilaWheelWidget extends StatelessWidget {
  final List<LilaPeriod> periods;
  final int selectedPeriodId;
  final ValueChanged<int> onPeriodSelected;

  const LilaWheelWidget({
    super.key,
    required this.periods,
    required this.selectedPeriodId,
    required this.onPeriodSelected,
  });

  void _handleTapUp(TapUpDetails details, Size size) {
    if (periods.isEmpty) return;

    final center = Offset(size.width / 2, size.height / 2);
    final touch = details.localPosition;
    final dx = touch.dx - center.dx;
    final dy = touch.dy - center.dy;

    final distance = math.sqrt(dx * dx + dy * dy);
    final outerRadius = size.width / 2;
    final innerRadius = outerRadius * 0.35;

    if (distance < innerRadius || distance > outerRadius) return;

    double angle = math.atan2(dy, dx) + math.pi / 2;
    if (angle < 0) angle += 2 * math.pi;

    final sliceAngle = (2 * math.pi) / periods.length;
    int tappedIndex = (angle / sliceAngle).floor() % periods.length;

    onPeriodSelected(periods[tappedIndex].id);
  }

  @override
  Widget build(BuildContext context) {
    if (periods.isEmpty) {
      return const SizedBox.shrink();
    }

    return AspectRatio(
      aspectRatio: 1.0,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final size = Size(constraints.maxWidth, constraints.maxHeight);
          return GestureDetector(
            onTapUp: (details) => _handleTapUp(details, size),
            child: CustomPaint(
              size: size,
              painter: _WheelPainter(
                selectedId: selectedPeriodId,
                periods: periods,
                isDark: Theme.of(context).brightness == Brightness.dark,
              ),
            ),
          );
        },
      ),
    );
  }
}

class _WheelPainter extends CustomPainter {
  final int selectedId;
  final List<LilaPeriod> periods;
  final bool isDark;

  _WheelPainter({
    required this.selectedId,
    required this.periods,
    required this.isDark,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final count = periods.length;
    if (count == 0) return;

    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;
    final innerRadius = radius * 0.35;
    final sliceAngle = (2 * math.pi) / count;

    final baseColor = isDark ? BssColors.darkOakCard : BssColors.parchmentCard;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;

    for (int i = 0; i < count; i++) {
      final period = periods[i];
      final isSelected = (period.id == selectedId);
      final startAngle = (i * sliceAngle) - (math.pi / 2);

      final path = Path()
        ..moveTo(
          center.dx + innerRadius * math.cos(startAngle),
          center.dy + innerRadius * math.sin(startAngle),
        )
        ..arcTo(
          Rect.fromCircle(center: center, radius: radius),
          startAngle,
          sliceAngle,
          false,
        )
        ..lineTo(
          center.dx + innerRadius * math.cos(startAngle + sliceAngle),
          center.dy + innerRadius * math.sin(startAngle + sliceAngle),
        )
        ..arcTo(
          Rect.fromCircle(center: center, radius: innerRadius),
          startAngle + sliceAngle,
          -sliceAngle,
          false,
        )
        ..close();

      final fillPaint = Paint()
        ..style = PaintingStyle.fill
        ..color = isSelected ? goldColor : baseColor;
      canvas.drawPath(path, fillPaint);

      final borderPaint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.0
        ..color = goldColor.withValues(alpha: 0.6);
      canvas.drawPath(path, borderPaint);

      final midAngle = startAngle + (sliceAngle / 2);
      final textRadius = (radius + innerRadius) / 2;
      final textCenter = Offset(
        center.dx + textRadius * math.cos(midAngle),
        center.dy + textRadius * math.sin(midAngle),
      );

      final textPainter = TextPainter(
        text: TextSpan(
          text: '${i + 1}\n${period.title}\n${period.timeRange}',
          style: TextStyle(
            color: isSelected && !isDark ? Colors.white : textColor,
            fontSize: radius * 0.075,
            fontWeight: FontWeight.bold,
            height: 1.2,
          ),
        ),
        textAlign: TextAlign.center,
        textDirection: TextDirection.ltr,
      )..layout();

      textPainter.paint(
        canvas,
        textCenter - Offset(textPainter.width / 2, textPainter.height / 2),
      );
    }

    final ringPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0
      ..color = goldColor;

    canvas.drawCircle(center, radius, ringPaint);
    canvas.drawCircle(center, innerRadius, ringPaint);
  }

  @override
  bool shouldRepaint(covariant _WheelPainter oldDelegate) {
    return oldDelegate.selectedId != selectedId ||
        oldDelegate.periods != periods ||
        oldDelegate.isDark != isDark;
  }
}