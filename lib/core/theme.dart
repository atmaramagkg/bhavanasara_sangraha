import 'package:flutter/material.dart';

/// Warm, illuminated-manuscript palette matching the app's design mockups:
/// cream/gold in light mode, deep brown/gold in dark mode.
class AppColors {
  AppColors._();

  // Light theme
  static const Color lightBackground = Color(0xFFFBF3E3);
  static const Color lightSurface = Color(0xFFFFFDF8);
  static const Color lightCard = Color(0xFFFFFBF0);
  static const Color gold = Color(0xFFC9922E);
  static const Color goldDeep = Color(0xFF9C6B14);
  static const Color inkBrown = Color(0xFF3B2A1A);
  static const Color inkBrownSoft = Color(0xFF6B5842);

  // Dark theme
  static const Color darkBackground = Color(0xFF241B12);
  static const Color darkSurface = Color(0xFF2E2418);
  static const Color darkCard = Color(0xFF362A1B);
  static const Color creamText = Color(0xFFF3E7D0);
  static const Color creamTextSoft = Color(0xFFC9B896);
}

class AppTheme {
  AppTheme._();

  static ThemeData light() {
    final ColorScheme scheme = ColorScheme.fromSeed(
      seedColor: AppColors.gold,
      brightness: Brightness.light,
    ).copyWith(
      primary: AppColors.goldDeep,
      secondary: AppColors.gold,
      surface: AppColors.lightSurface,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: AppColors.lightBackground,
      fontFamily: 'NotoSerif',
      textTheme: _textTheme(AppColors.inkBrown, AppColors.inkBrownSoft),
      cardTheme: const CardThemeData(
        color: AppColors.lightCard,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(14)),
          side: BorderSide(color: Color(0x33C9922E)),
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.lightBackground,
        foregroundColor: AppColors.inkBrown,
        elevation: 0,
        centerTitle: true,
      ),
      dividerColor: const Color(0x33C9922E),
    );
  }

  static ThemeData dark() {
    final ColorScheme scheme = ColorScheme.fromSeed(
      seedColor: AppColors.gold,
      brightness: Brightness.dark,
    ).copyWith(
      primary: AppColors.gold,
      secondary: AppColors.gold,
      surface: AppColors.darkSurface,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: AppColors.darkBackground,
      fontFamily: 'NotoSerif',
      textTheme: _textTheme(AppColors.creamText, AppColors.creamTextSoft),
      cardTheme: const CardThemeData(
        color: AppColors.darkCard,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(14)),
          side: BorderSide(color: Color(0x33C9922E)),
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.darkBackground,
        foregroundColor: AppColors.creamText,
        elevation: 0,
        centerTitle: true,
      ),
      dividerColor: const Color(0x33C9922E),
    );
  }

  static TextTheme _textTheme(Color strong, Color soft) {
    return TextTheme(
      headlineSmall: TextStyle(color: strong, fontWeight: FontWeight.w600),
      titleLarge: TextStyle(color: strong, fontWeight: FontWeight.w600),
      titleMedium: TextStyle(color: strong, fontWeight: FontWeight.w600),
      bodyLarge: TextStyle(color: strong, height: 1.5),
      bodyMedium: TextStyle(color: soft, height: 1.4),
      bodySmall: TextStyle(color: soft),
      labelLarge: TextStyle(color: strong),
    );
  }
}
