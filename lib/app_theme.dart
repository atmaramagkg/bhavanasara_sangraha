// app_theme.dart
import 'package:flutter/material.dart';

class BssColors {
  // Parchment Theme Palette
  static const Color parchmentBg = Color(0xFFF5EFE0);
  static const Color parchmentCard = Color(0xFFEFE3C9);
  static const Color goldAccent = Color(0xFFD4AF37);
  static const Color goldDark = Color(0xFFA67C1E);
  static const Color darkText = Color(0xFF2C1A0E);
  static const Color sanskritText = Color(0xFF7A2E20);
  static const Color subText = Color(0xFF6E5D4F);

  // Dark Oak Theme Palette
  static const Color darkOakBg = Color(0xFF1A120B);
  static const Color darkOakCard = Color(0xFF2B1E16);
  static const Color darkOakGold = Color(0xFFE6C280);
  static const Color darkOakText = Color(0xFFEDE0D4);
  static const Color darkOakSanskritText = Color(0xFFC89888);
  static const Color darkOakSubText = Color(0xFFA08D7D);
}

class BssTheme {
  // Light / Parchment ThemeData
  static ThemeData parchmentTheme([String fontFamily = 'NotoSerif']) {
    return ThemeData(
      brightness: Brightness.light,
      scaffoldBackgroundColor: BssColors.parchmentBg,
      primaryColor: BssColors.goldAccent,
      cardColor: BssColors.parchmentCard,
      fontFamily: fontFamily,
      colorScheme: const ColorScheme.light(
        primary: BssColors.goldAccent,
        surface: BssColors.parchmentCard,
        onSurface: BssColors.darkText,
      ),
      textTheme: TextTheme(
        headlineMedium: TextStyle(
          color: BssColors.darkText,
          fontWeight: FontWeight.bold,
          fontFamily: fontFamily,
        ),
        bodyLarge: TextStyle(
          color: BssColors.darkText,
          fontSize: 16.0,
          fontFamily: fontFamily,
        ),
        bodyMedium: TextStyle(
          color: BssColors.subText,
          fontSize: 14.0,
          fontFamily: fontFamily,
        ),
      ),
    );
  }

  // Dark / Dark Oak ThemeData
  static ThemeData darkOakTheme([String fontFamily = 'NotoSerif']) {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: BssColors.darkOakBg,
      primaryColor: BssColors.darkOakGold,
      cardColor: BssColors.darkOakCard,
      fontFamily: fontFamily,
      colorScheme: const ColorScheme.dark(
        primary: BssColors.darkOakGold,
        surface: BssColors.darkOakCard,
        onSurface: BssColors.darkOakText,
      ),
      textTheme: TextTheme(
        headlineMedium: TextStyle(
          color: BssColors.darkOakText,
          fontWeight: FontWeight.bold,
          fontFamily: fontFamily,
        ),
        bodyLarge: TextStyle(
          color: BssColors.darkOakText,
          fontSize: 16.0,
          fontFamily: fontFamily,
        ),
        bodyMedium: TextStyle(
          color: BssColors.darkOakSubText,
          fontSize: 14.0,
          fontFamily: fontFamily,
        ),
      ),
    );
  }
}