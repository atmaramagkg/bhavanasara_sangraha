import 'package:flutter/material.dart';

class QuoteCard extends StatelessWidget {
  final String quoteText;
  final String citationText;
  final VoidCallback? onCitationTap;

  const QuoteCard({
    super.key,
    required this.quoteText,
    required this.citationText,
    this.onCitationTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(
        horizontal: 12,
        vertical: 6,
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              quoteText,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerRight,
              child: ActionChip(
                label: Text(citationText),
                onPressed: onCitationTap,
              ),
            ),
          ],
        ),
      ),
    );
  }
}