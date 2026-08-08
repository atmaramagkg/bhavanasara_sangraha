// services/app_settings.dart
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// App-wide preferences: theme mode and bookmarked sections.
/// Backed by SharedPreferences, exposed as ValueNotifiers so any widget
/// can listen without needing a state-management package wired through
/// the whole tree.
class AppSettings {
  AppSettings._();

  static const _themeModeKey = 'bss_theme_mode';
  static const _bookmarksKey = 'bss_bookmarked_section_ids';
  static const _fontScaleKey = 'bss_font_scale';
  static const _localeKey = 'bss_locale';

  static const double minFontScale = 0.85;
  static const double maxFontScale = 1.6;

  static final ValueNotifier<ThemeMode> themeMode =
      ValueNotifier<ThemeMode>(ThemeMode.system);

  static final ValueNotifier<Set<int>> bookmarkedSectionIds =
      ValueNotifier<Set<int>>(<int>{});

  static final ValueNotifier<double> fontScale = ValueNotifier<double>(1.0);

  /// Currently selected UI language. Defaults to English so the app always
  /// opens in English on first launch regardless of the device locale.
  static final ValueNotifier<Locale> locale = ValueNotifier<Locale>(
    const Locale('en'),
  );

  static bool _loaded = false;

  /// Must be called once before runApp() so the first frame already
  /// reflects saved preferences instead of flashing the defaults.
  static Future<void> load() async {
    if (_loaded) return;
    final prefs = await SharedPreferences.getInstance();

    final int savedIndex = prefs.getInt(_themeModeKey) ?? ThemeMode.system.index;
    themeMode.value = ThemeMode.values[savedIndex.clamp(0, ThemeMode.values.length - 1)];

    final List<String> savedBookmarks = prefs.getStringList(_bookmarksKey) ?? const [];
    bookmarkedSectionIds.value = savedBookmarks
        .map((s) => int.tryParse(s))
        .whereType<int>()
        .toSet();

    final double? savedScale = prefs.getDouble(_fontScaleKey);
    if (savedScale != null) {
      fontScale.value = savedScale.clamp(minFontScale, maxFontScale);
    }

    final String? savedLocale = prefs.getString(_localeKey);
    if (savedLocale != null) {
      locale.value = Locale(savedLocale);
    }

    _loaded = true;
  }

  static Future<void> setThemeMode(ThemeMode mode) async {
    themeMode.value = mode;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_themeModeKey, mode.index);
  }

  static Future<void> setFontScale(double scale) async {
    final double clamped = scale.clamp(minFontScale, maxFontScale);
    fontScale.value = clamped;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble(_fontScaleKey, clamped);
  }

  static Future<void> setLocale(Locale next) async {
    locale.value = next;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_localeKey, next.languageCode);
  }

  static bool isBookmarked(int sectionId) =>
      bookmarkedSectionIds.value.contains(sectionId);

  static Future<void> toggleBookmark(int sectionId) async {
    final Set<int> updated = Set<int>.from(bookmarkedSectionIds.value);
    if (!updated.remove(sectionId)) {
      updated.add(sectionId);
    }
    bookmarkedSectionIds.value = updated;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(
      _bookmarksKey,
      updated.map((id) => id.toString()).toList(),
    );
  }
}
