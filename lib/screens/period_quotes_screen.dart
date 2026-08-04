import 'package:flutter/material.dart';

class PeriodQuotesScreen extends StatelessWidget {
  final Map<String, dynamic> period;

  const PeriodQuotesScreen({
    super.key,
    required this.period,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(period['name'] as String),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            "Quotes for ${period['name']} will appear here.",
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }
}