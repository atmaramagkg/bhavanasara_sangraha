import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'app_theme.dart';
import 'screens/home_screen.dart';
import 'services/app_settings.dart';
import 'services/translations.dart';

class LilaSmaranaApp extends StatelessWidget {
  const LilaSmaranaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: AppSettings.themeMode,
      builder: (context, mode, _) {
        return ValueListenableBuilder<Locale>(
          valueListenable: AppSettings.locale,
          builder: (context, locale, _) {
            return ValueListenableBuilder<String>(
              valueListenable: AppSettings.fontFamily,
              builder: (context, fontFamily, _) {
                return MaterialApp(
                  title: Translations.t('app.title'),
                  debugShowCheckedModeBanner: false,
                  theme: BssTheme.parchmentTheme(fontFamily),
                  darkTheme: BssTheme.darkOakTheme(fontFamily),
                  themeMode: mode,
                  locale: locale,
                  localizationsDelegates: const [
                    GlobalMaterialLocalizations.delegate,
                    GlobalWidgetsLocalizations.delegate,
                    GlobalCupertinoLocalizations.delegate,
                  ],
                  supportedLocales: const [
                    Locale('en'),
                    Locale('ru'),
                    Locale('hi'),
                  ],
                  // Remount on language change so every screen re-reads its
                  // translated content from the in-memory translation map.
                  home: HomeScreen(key: ValueKey(locale.languageCode)),
                );
              },
            );
          },
        );
      },
    );
  }
}
