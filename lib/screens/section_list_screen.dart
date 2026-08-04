import 'package:flutter/material.dart';

import '../core/database/app_database.dart';
import 'quote_list_screen.dart';

class SectionListScreen extends StatelessWidget {
  final Map<String, dynamic> subPeriod;

  const SectionListScreen({super.key, required this.subPeriod});

  @override
  Widget build(BuildContext context) {
    final int subPeriodId = subPeriod['id'] as int;
    final String subPeriodName = subPeriod['name'] as String? ?? '';

    return Scaffold(
      appBar: AppBar(title: Text(subPeriodName)),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: AppDatabase.instance.getSections(subPeriodId),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(child: Text('Database error: ${snapshot.error}'));
          }

          final List<Map<String, dynamic>> sections = snapshot.data ?? [];

          if (sections.isEmpty) {
            return const Center(
              child: Text('No sections yet for this subperiod.'),
            );
          }

          return ListView.separated(
            itemCount: sections.length,
            separatorBuilder: (_, _) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final Map<String, dynamic> section = sections[index];

              return ListTile(
                leading: CircleAvatar(child: Text('${section['sort_order']}')),
                title: Text(section['title'] as String? ?? ''),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => QuoteListScreen(section: section),
                    ),
                  );
                },
              );
            },
          );
        },
      ),
    );
  }
}
