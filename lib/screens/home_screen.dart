import 'package:flutter/material.dart';
import '../core/database/app_database.dart';
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

        // Always open on whichever period (main + sub) the clock says it is
        // right now -- that's the whole point of a time-of-day devotional
        // reader. This runs on every cold start and every language switch
        // (which remounts this widget), so the app never opens "stale" on
        // a period from hours or days ago.
        //
        // NOTE: AppSettings.lastReadSectionId is intentionally NOT used to
        // pick the initial screen here. It used to take priority over the
        // live time-of-day lookup, which meant that after the very first
        // launch (once any section had ever been read), the app would keep
        // reopening on the last-read section forever, and the current-time
        // logic below would never run again. Deep links / explicit
        // navigation can still jump to a specific section via
        // ReadingScreen's initialSectionId; this entry point just no
        // longer does so automatically on plain app open.
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
