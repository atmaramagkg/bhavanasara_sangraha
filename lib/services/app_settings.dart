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
  static const _fontFamilyKey = 'bss_font_family';
  static const _lastReadSectionKey = 'bss_last_read_section_id';

  static const double minFontScale = 0.85;
  static const double maxFontScale = 1.6;

  /// The two bundled font families (see pubspec `fonts` section).
  static const String fontSerif = 'NotoSerif';
  static const String fontSans = 'NotoSans';

  static final ValueNotifier<ThemeMode> themeMode =
      ValueNotifier<ThemeMode>(ThemeMode.system);

  static final ValueNotifier<Set<int>> bookmarkedSectionIds =
      ValueNotifier<Set<int>>(<int>{});

  static final ValueNotifier<double> fontScale = ValueNotifier<double>(1.0);

  /// Currently selected font family, used by the app-wide theme.
  static final ValueNotifier<String> fontFamily =
      ValueNotifier<String>(fontSerif);

  /// Currently selected UI language. Defaults to English so the app always
  /// opens in English on first launch regardless of the device locale.
  static final ValueNotifier<Locale> locale = ValueNotifier<Locale>(
    const Locale('en'),
  );

  /// The section the user was last reading, so the app can resume there --
  /// both on a normal relaunch and immediately after a language switch,
  /// which needs to reopen the reading screen from scratch against the
  /// newly-selected language's database.
  static final ValueNotifier<int?> lastReadSectionId = ValueNotifier<int?>(null);

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

    final String? savedFontFamily = prefs.getString(_fontFamilyKey);
    if (savedFontFamily != null &&
        (savedFontFamily == fontSerif || savedFontFamily == fontSans)) {
      fontFamily.value = savedFontFamily;
    }

    lastReadSectionId.value = prefs.getInt(_lastReadSectionKey);

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

  static Future<void> setFontFamily(String family) async {
    fontFamily.value = family;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_fontFamilyKey, family);
  }

  /// Cheap, fire-and-forget: called on every real section change (not on
  /// every scroll tick) so relaunching, or switching language, resumes
  /// close to where the user actually was.
  static Future<void> setLastReadSection(int sectionId) async {
    lastReadSectionId.value = sectionId;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_lastReadSectionKey, sectionId);
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
