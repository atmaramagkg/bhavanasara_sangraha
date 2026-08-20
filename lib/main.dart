import 'package:flutter/material.dart';

import 'app.dart';
import 'core/database/app_database.dart';
import 'services/app_settings.dart';
import 'services/translations.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await AppSettings.load();
  // Open the single unified database.
  await AppDatabase.instance.init();
  await Translations.load();

  runApp(
    const LilaSmaranaApp(),
  );
}
