import 'package:flutter/material.dart';

import 'app_theme.dart';
import 'screens/home_screen.dart';
import 'services/app_settings.dart';

class BhavanasaraApp extends StatelessWidget {
  const BhavanasaraApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: AppSettings.themeMode,
      builder: (context, mode, _) {
        return MaterialApp(
          title: 'Bhāvanāsāra Saṅgraha',
          debugShowCheckedModeBanner: false,
          theme: BssTheme.parchmentTheme,
          darkTheme: BssTheme.darkOakTheme,
          themeMode: mode,
          home: const HomeScreen(),
        );
      },
    );
  }
}
