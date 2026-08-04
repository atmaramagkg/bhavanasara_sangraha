import 'package:flutter/material.dart';

import 'screens/home_screen.dart';

class BhavanasaraApp extends StatelessWidget {
  const BhavanasaraApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Bhāvanāsāra Saṅgraha',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF7A3F00),
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF7A3F00),
        brightness: Brightness.dark,
      ),
      home: const HomeScreen(),
    );
  }
}