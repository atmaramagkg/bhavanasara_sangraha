import 'package:flutter/material.dart';
import '../core/database/app_database.dart';
import '../services/app_settings.dart';
import '../services/bss_repository.dart';
import 'reading_screen.dart';

// Note: this screen doesn't need to listen to AppSettings.locale itself --
// app.dart already keys HomeScreen by language code, so the whole subtree
// (including this widget) gets freshly torn down and rebuilt on a language
// switch. That guarantees a brand-new BssRepository against the correct
// database file rather than one holding a stale, closed connection.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder(
      future: AppDatabase.instance.database,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        if (snapshot.hasError) {
          return Scaffold(
            body: Center(child: Text('Database Error: ${snapshot.error}')),
          );
        }

        final db = snapshot.data;
        if (db == null) {
          return const Scaffold(
            body: Center(child: Text('Failed to load database instance.')),
          );
        }

        final repository = BssRepository(db);

        // Prefer resuming exactly where the user left off -- whether that's
        // from a normal relaunch, or immediately after a language switch,
        // which remounts this whole screen from scratch. Only fall back to
        // "whatever period it is right now" when there's truly no saved
        // position yet (first-ever launch).
        final int? resumeSectionId = AppSettings.lastReadSectionId.value;
        if (resumeSectionId != null) {
          return ReadingScreen(
            repository: repository,
            initialSectionId: resumeSectionId,
          );
        }

        // Open on whichever period (main + sub) the clock says it is right
        // now, falling back to period 1 if that lookup ever fails.
        return FutureBuilder<({int mainPeriodId, int subPeriodId})?>(
          future: repository.getCurrentPeriodPair(),
          builder: (context, periodSnapshot) {
            if (periodSnapshot.connectionState == ConnectionState.waiting) {
              return const Scaffold(
                body: Center(child: CircularProgressIndicator()),
              );
            }

            final current = periodSnapshot.data;
            return ReadingScreen(
              repository: repository,
              initialPeriodId: current?.mainPeriodId ?? 1,
              initialSubPeriodId: current?.subPeriodId,
            );
          },
        );
      },
    );
  }
}
