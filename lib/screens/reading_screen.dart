import 'package:flutter/material.dart';
import 'package:scrollable_positioned_list/scrollable_positioned_list.dart';
import 'package:share_plus/share_plus.dart';
import '../app_theme.dart';
import '../models/lila_period.dart';
import '../services/app_settings.dart';
import '../services/bss_repository.dart';
import '../services/translations.dart';
import '../widgets/app_menu_sheet.dart';
import '../utils/text_utils.dart';
import 'book_reader_screen.dart';
import 'bookmarks_screen.dart';
import 'books_screen.dart';
import 'period_screen.dart';
import 'search_screen.dart';
import 'verse_detail_screen.dart';

class ReadingScreen extends StatefulWidget {
  final BssRepository repository;
  final int initialPeriodId;
  final int? initialSubPeriodId;
  final int? initialSectionId;

  const ReadingScreen({
    super.key,
    required this.repository,
    this.initialPeriodId = 1,
    this.initialSubPeriodId,
    this.initialSectionId,
  });

  @override
  State<ReadingScreen> createState() => _ReadingScreenState();
}

class _ReadingScreenState extends State<ReadingScreen> {
  // ItemScrollController scrolls to an index directly -- it does not need
  // the target item to already be built, so it works reliably no matter
  // how far away the target is, unlike Scrollable.ensureVisible + GlobalKey.
  final ItemScrollController _itemScrollController = ItemScrollController();
  final ItemPositionsListener _itemPositionsListener =
      ItemPositionsListener.create();

  List<LilaPeriod> _mainPeriods = [];
  List<SubPeriod> _currentSubPeriods = [];
  List<ContinuousReadingItem> _feedItems = [];

  int _selectedMainPeriodId = 1;
  int _selectedSubPeriodId = -1;
  int _selectedSectionId = -1;
  int? _highlightedVerseId;
  String? _highlightQuery;
  String _lastSearchQuery = '';
  final GlobalKey _highlightedQuoteKey = GlobalKey();
  final ScrollController _subPeriodScrollController = ScrollController();
  bool _isLoading = true;
  bool _isProgrammaticScroll = false;

  @override
  void initState() {
    super.initState();
    _selectedMainPeriodId = widget.initialPeriodId;
    _itemPositionsListener.itemPositions.addListener(_onPositionsChanged);
    _initializeData();
  }

  @override
  void dispose() {
    _itemPositionsListener.itemPositions.removeListener(_onPositionsChanged);
    _subPeriodScrollController.dispose();
    super.dispose();
  }

  Future<void> _initializeData() async {
    if (!mounted) return;
    setState(() => _isLoading = true);

    try {
      final List<LilaPeriod> mainPeriods = await widget.repository.getMainPeriods();
      final List<ContinuousReadingItem> feedItems = await widget.repository.loadFullContinuousFeed();

      if (!mounted) return;

      _mainPeriods = mainPeriods;
      _feedItems = feedItems;

      int initialIndex = 0;
      if (feedItems.isNotEmpty) {
        // Priority: an exact resumed section (deep link or language switch)
        // > the precise sub period the clock says it is right now (e.g.
        // nishanta_2 instead of nishanta_1) > just the main period > the
        // very first item, in that order.
        final int? targetSectionId = widget.initialSectionId;
        initialIndex = targetSectionId != null
            ? feedItems.indexWhere((item) => item.section.id == targetSectionId)
            : -1;

        if (initialIndex == -1) {
          final int? targetSubPeriodId = widget.initialSubPeriodId;
          initialIndex = targetSubPeriodId != null
              ? feedItems.indexWhere(
                  (item) => item.subPeriod.id == targetSubPeriodId,
                )
              : -1;
        }
        if (initialIndex == -1) {
          initialIndex = feedItems.indexWhere(
            (item) => item.mainPeriod.id == _selectedMainPeriodId,
          );
        }
        if (initialIndex == -1) initialIndex = 0;

        final targetItem = feedItems[initialIndex];
        _selectedMainPeriodId = targetItem.mainPeriod.id;
        _selectedSubPeriodId = targetItem.subPeriod.id;
        _selectedSectionId = targetItem.section.id;
      }

      final subPeriods = await widget.repository.getSubPeriods(_selectedMainPeriodId);
      if (!mounted) return;

      setState(() {
        _currentSubPeriods = subPeriods;
        if (!subPeriods.any((s) => s.id == _selectedSubPeriodId) && subPeriods.isNotEmpty) {
          _selectedSubPeriodId = subPeriods.first.id;
        }
        _isLoading = false;
      });

      if (feedItems.isNotEmpty) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          _itemScrollController.jumpTo(index: initialIndex);
          _scrollSubPeriodBarToSelected();
        });
      }
    } catch (e) {
      debugPrint('Error initializing data: $e');
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  /// Keeps the top tabs / subperiod bar / right rail in sync with whatever
  /// section the user has scrolled to manually (not via a button tap).
  void _onPositionsChanged() {
    if (_isProgrammaticScroll || _feedItems.isEmpty) return;

    final positions = _itemPositionsListener.itemPositions.value;
    if (positions.isEmpty) return;

    // The topmost item that's still at least partially visible.
    final ItemPosition topMost = positions
        .where((p) => p.itemTrailingEdge > 0)
        .reduce((a, b) => a.itemLeadingEdge < b.itemLeadingEdge ? a : b);

    if (topMost.index < 0 || topMost.index >= _feedItems.length) return;

    final item = _feedItems[topMost.index];
    if (item.section.id == _selectedSectionId) return;

    _updateActiveNavigationSilently(item.mainPeriod.id, item.subPeriod.id, item.section.id);
  }

  Future<void> _updateActiveNavigationSilently(int mainId, int subId, int secId) async {
    List<SubPeriod> subPeriods = _currentSubPeriods;
    final bool mainChanged = mainId != _selectedMainPeriodId;
    if (mainChanged) {
      subPeriods = await widget.repository.getSubPeriods(mainId);
    }
    if (!mounted) return;

    setState(() {
      _selectedMainPeriodId = mainId;
      _selectedSubPeriodId = subId;
      _selectedSectionId = secId;
      if (mainChanged) {
        _currentSubPeriods = subPeriods;
      }
    });
    AppSettings.setLastReadSection(secId);

    _scrollSubPeriodBarToSelected();
  }

  void _scrollSubPeriodBarToSelected() {
    if (!_subPeriodScrollController.hasClients) return;
    final index = _currentSubPeriods.indexWhere(
      (s) => s.id == _selectedSubPeriodId,
    );
    if (index == -1) return;
    // Each sub-period chip is roughly 80px wide (padding + margin + text).
    final targetOffset = (index * 80.0) - 80.0;
    _subPeriodScrollController.animateTo(
      targetOffset.clamp(
        0.0,
        _subPeriodScrollController.position.maxScrollExtent,
      ),
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeInOut,
    );
  }

  /// Scrolls the feed so the given section's title lands near the top.
  /// Index-based, so it works whether or not the item has ever been built.
  Future<void> _scrollToSection(int sectionId, {bool animate = true}) async {
    final index = _feedItems.indexWhere((item) => item.section.id == sectionId);
    if (index == -1) {
      debugPrint('Section $sectionId not found in feed');
      return;
    }

    _isProgrammaticScroll = true;

    if (animate) {
      await _itemScrollController.scrollTo(
        index: index,
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeInOut,
        alignment: 0.02,
      );
    } else {
      _itemScrollController.jumpTo(index: index, alignment: 0.02);
    }

    // Small settle delay so the position listener doesn't immediately
    // fight the button-driven selection with its own read of the scroll.
    await Future.delayed(const Duration(milliseconds: 150));
    _isProgrammaticScroll = false;
  }

  Future<void> _onMainPeriodTabSelected(int mainPeriodId) async {
    final subPeriods = await widget.repository.getSubPeriods(mainPeriodId);

    final targetIndex = _feedItems.indexWhere((item) => item.mainPeriod.id == mainPeriodId);
    if (targetIndex == -1) return;
    final targetItem = _feedItems[targetIndex];

    if (!mounted) return;

    setState(() {
      _selectedMainPeriodId = mainPeriodId;
      _currentSubPeriods = subPeriods;
      _selectedSubPeriodId = targetItem.subPeriod.id;
      _selectedSectionId = targetItem.section.id;
      _highlightedVerseId = null;
      _highlightQuery = null;
    });

    _scrollToSection(targetItem.section.id);
    AppSettings.setLastReadSection(targetItem.section.id);
    WidgetsBinding.instance.addPostFrameCallback((_) => _scrollSubPeriodBarToSelected());
  }

  Future<void> _onSubPeriodSelected(int subPeriodId) async {
    final targetIndex = _feedItems.indexWhere((item) => item.subPeriod.id == subPeriodId);
    if (targetIndex == -1) return;
    final targetItem = _feedItems[targetIndex];

    if (!mounted) return;

    setState(() {
      _selectedSubPeriodId = subPeriodId;
      _selectedMainPeriodId = targetItem.mainPeriod.id;
      _selectedSectionId = targetItem.section.id;
      _highlightedVerseId = null;
      _highlightQuery = null;
    });

    _scrollToSection(targetItem.section.id);
    AppSettings.setLastReadSection(targetItem.section.id);
  }

  void _onSectionRailSelected(int sectionId) {
    setState(() {
      _selectedSectionId = sectionId;
      _highlightedVerseId = null;
      _highlightQuery = null;
    });
    _scrollToSection(sectionId);
    AppSettings.setLastReadSection(sectionId);
  }

  /// Jumps to an arbitrary section that might belong to a *different* main
  /// period than the one currently open -- used by search results and
  /// bookmarks, unlike the rail/tab handlers above which only ever jump
  /// within the period already on screen.
  Future<void> _jumpToSection(int sectionId) async {
    final targetIndex = _feedItems.indexWhere((item) => item.section.id == sectionId);
    if (targetIndex == -1) return;
    final targetItem = _feedItems[targetIndex];

    final bool mainPeriodChanged = targetItem.mainPeriod.id != _selectedMainPeriodId;
    final List<SubPeriod> subPeriods = mainPeriodChanged
        ? await widget.repository.getSubPeriods(targetItem.mainPeriod.id)
        : _currentSubPeriods;

    if (!mounted) return;

    setState(() {
      _selectedMainPeriodId = targetItem.mainPeriod.id;
      _selectedSubPeriodId = targetItem.subPeriod.id;
      _selectedSectionId = targetItem.section.id;
      _currentSubPeriods = subPeriods;
      // Callers that want a highlight (search) set it themselves right
      // after this returns; every other caller (bookmarks) wants none.
      _highlightedVerseId = null;
      _highlightQuery = null;
    });

    await _scrollToSection(sectionId);
    AppSettings.setLastReadSection(sectionId);
  }

  /// Renders a verse's translation text (or transliteration fallback),
  /// highlighting the search match if this is the verse the user just
  /// navigated here from search to look at.
  Widget _buildVerseText(VerseDetail verse, Color textColor, Color goldColor) {
    final langCode = AppSettings.locale.value.languageCode;
    String text = verse.translationForCode(langCode);
    // Fall back to transliteration when no translation in current language.
    if (text.isEmpty && verse.transliteration.isNotEmpty) {
      text = verse.transliteration;
    }
    if (text.isEmpty) return const SizedBox.shrink();

    final sanskritColor = Theme.of(context).brightness == Brightness.dark
        ? BssColors.darkOakSanskritText
        : BssColors.sanskritText;
    final baseStyle = TextStyle(fontSize: 13, color: sanskritColor);

    if (_highlightedVerseId == null ||
        verse.verseId != _highlightedVerseId ||
        _highlightQuery == null) {
      return Text(text, style: baseStyle);
    }

    final String normalizedText = normalizeForSearch(text);
    final String normalizedQuery = normalizeForSearch(_highlightQuery!);
    final int matchIndex = normalizedQuery.isEmpty ? -1 : normalizedText.indexOf(normalizedQuery);

    if (matchIndex == -1) {
      return Text(text, style: baseStyle);
    }

    final String before = text.substring(0, matchIndex);
    final String matched = text.substring(matchIndex, matchIndex + normalizedQuery.length);
    final String after = text.substring(matchIndex + normalizedQuery.length);

    return RichText(
      text: TextSpan(
        style: baseStyle,
        children: [
          TextSpan(text: before),
          TextSpan(
            text: matched,
            style: TextStyle(
              backgroundColor: goldColor.withAlpha(90),
              fontWeight: FontWeight.bold,
              color: sanskritColor,
            ),
          ),
          TextSpan(text: after),
        ],
      ),
    );
  }

  void _openPeriodInfoSheet() async {
    final ({int mainPeriodId, int subPeriodId})? currentPair =
        await widget.repository.getCurrentPeriodPair();
    final int? liveCurrentId = currentPair?.mainPeriodId;

    String? currentSubPeriodTitle;
    String? currentSubPeriodTimeRange;
    if (currentPair != null) {
      final List<SubPeriod> subPeriods =
          await widget.repository.getSubPeriods(currentPair.mainPeriodId);
      for (final sub in subPeriods) {
        if (sub.id == currentPair.subPeriodId) {
          currentSubPeriodTitle = sub.title;
          currentSubPeriodTimeRange = sub.timeRange;
          break;
        }
      }
    }
    if (!mounted) return;

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PeriodScreen(
          repository: widget.repository,
          periods: _mainPeriods,
          currentPeriodId: liveCurrentId ?? _selectedMainPeriodId,
          onPeriodSelected: _onMainPeriodTabSelected,
          currentSubPeriodTitle: currentSubPeriodTitle,
          currentSubPeriodTimeRange: currentSubPeriodTimeRange,
        ),
      ),
    );
  }

  void _openBooksScreen() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => BooksScreen(repository: widget.repository)),
    );
  }

  void _openVerseDetail(int verseId) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => VerseDetailScreen(
          repository: widget.repository,
          verseId: verseId,
        ),
      ),
    );
  }

  void _openBookBySlug(String slug) async {
    final book = await widget.repository.getBookBySlug(slug);
    if (book == null || !mounted) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => BookReaderScreen(
          repository: widget.repository,
          book: book,
        ),
      ),
    );
  }

  void _openSourceRefVerse(String sourceRefs) async {
    final parts = sourceRefs.split(' ');
    if (parts.length < 2) return;
    final slug = parts[0];
    final verseRef = parts.sublist(1).join(' ');
    final verseId = await widget.repository.getVerseIdByBookAndRef(slug, verseRef);
    if (verseId == null || !mounted) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => VerseDetailScreen(
          repository: widget.repository,
          verseId: verseId,
        ),
      ),
    );
  }

  void _openSearch() async {
    final SearchResult? result = await Navigator.of(context).push<SearchResult>(
      MaterialPageRoute(
        builder: (_) => SearchScreen(
          feedItems: _feedItems,
          initialQuery: _lastSearchQuery,
        ),
      ),
    );
    if (result == null) return;

    _lastSearchQuery = result.query;

    // Wait for the section-level scroll to actually finish before doing a
    // fine adjustment -- otherwise the two animations fight each other.
    await _jumpToSection(result.sectionId);
    if (!mounted) return;

    setState(() {
      _highlightedVerseId = result.verseId;
      _highlightQuery = result.query.trim().isEmpty ? null : result.query;
    });

    // The highlighted quote might be several quotes deep into a long
    // section, so landing on the section's title isn't enough to
    // guarantee it's actually on screen. Once the highlight rebuild has
    // been laid out (next frame), nudge it into view specifically.
    if (result.verseId != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _scrollHighlightIntoView());
    }
  }

  void _scrollHighlightIntoView() {
    final BuildContext? highlightContext = _highlightedQuoteKey.currentContext;
    if (highlightContext == null) return;

    Scrollable.ensureVisible(
      highlightContext,
      duration: const Duration(milliseconds: 350),
      curve: Curves.easeInOut,
      alignment: 0.25,
      alignmentPolicy: ScrollPositionAlignmentPolicy.explicit,
    );
  }

  void _openAppMenu() {
    showModalBottomSheet(
      context: context,
      // Transparent so the theme-reactive Material below repaints when the
      // theme changes (a fixed backgroundColor captured here would stay light
      // even after switching to dark oak).
      backgroundColor: Colors.transparent,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (sheetContext) => Material(
        color: Theme.of(sheetContext).scaffoldBackgroundColor,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        clipBehavior: Clip.antiAlias,
        child: AppMenuSheet(
          onOpenBookmarks: _openBookmarksScreen,
          onShare: _shareCurrentSection,
        ),
      ),
    );
  }

  void _openBookmarksScreen() async {
    final int? jumpToSectionId = await Navigator.of(context).push<int>(
      MaterialPageRoute(builder: (_) => BookmarksScreen(repository: widget.repository)),
    );
    if (jumpToSectionId != null) {
      _jumpToSection(jumpToSectionId);
    }
  }

  void _shareCurrentSection() {
    final item = _feedItems.firstWhere(
      (i) => i.section.id == _selectedSectionId,
      orElse: () => _feedItems.first,
    );

    final buffer = StringBuffer()
      ..writeln(item.section.title)
      ..writeln();
    for (final verse in item.verses) {
      String text = verse.translationForCode(AppSettings.locale.value.languageCode);
      if (text.isEmpty && verse.transliteration.isNotEmpty) {
        text = verse.transliteration;
      }
      if (text.isNotEmpty) {
        buffer.writeln(text);
      }
      final shareRef = verse.bookId != null
          ? verse.refDisplay
          : Translations.translateSourceRef(verse.sourceRefs);
      if (shareRef.isNotEmpty) {
        buffer.writeln('— $shareRef');
      }
      buffer.writeln();
    }
    buffer.write('Lila Smarana');

    SharePlus.instance.share(ShareParams(text: buffer.toString()));
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final cardBg = isDark ? BssColors.darkOakCard : BssColors.parchmentCard;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;

    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    final activeRailItems = _feedItems
        .where((item) => item.subPeriod.id == _selectedSubPeriodId)
        .toList();

    return Scaffold(
      appBar: AppBar(
        automaticallyImplyLeading: false,
        leadingWidth: 84,
        leading: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            IconButton(
              icon: const Icon(Icons.access_time),
              tooltip: Translations.t('common.periods'),
              onPressed: _mainPeriods.isEmpty ? null : _openPeriodInfoSheet,
              color: goldColor,
              disabledColor: goldColor.withAlpha(140),
              iconSize: 20,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 38, minHeight: 38),
              visualDensity: VisualDensity.compact,
            ),
            IconButton(
              icon: const Icon(Icons.menu_book_outlined),
              tooltip: Translations.t('common.scriptures'),
              onPressed: _openBooksScreen,
              color: goldColor,
              disabledColor: goldColor.withAlpha(140),
              iconSize: 20,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 38, minHeight: 38),
              visualDensity: VisualDensity.compact,
            ),
          ],
        ),
        title: null,
        actions: [
          ValueListenableBuilder<Set<int>>(
            valueListenable: AppSettings.bookmarkedSectionIds,
            builder: (context, bookmarks, _) {
              final bool isBookmarked = bookmarks.contains(_selectedSectionId);
              return IconButton(
                icon: Icon(isBookmarked ? Icons.bookmark : Icons.bookmark_border),
                tooltip: isBookmarked
                    ? Translations.t('common.bookmark.remove')
                    : Translations.t('common.bookmark.add'),
                onPressed: _selectedSectionId == -1
                    ? null
                    : () => AppSettings.toggleBookmark(_selectedSectionId),
                color: goldColor,
                disabledColor: goldColor.withAlpha(140),
                iconSize: 20,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 38, minHeight: 38),
                visualDensity: VisualDensity.compact,
              );
            },
          ),
          const SizedBox(width: 2),
          IconButton(
            icon: const Icon(Icons.search),
            tooltip: Translations.t('screen.search.submit'),
            onPressed: _openSearch,
            color: goldColor,
            disabledColor: goldColor.withAlpha(140),
            iconSize: 20,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 38, minHeight: 38),
            visualDensity: VisualDensity.compact,
          ),
          const SizedBox(width: 4),
          IconButton(
            icon: const Icon(Icons.menu),
            tooltip: Translations.t('common.menu'),
            onPressed: _openAppMenu,
            color: goldColor,
            disabledColor: goldColor.withAlpha(140),
            iconSize: 20,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 38, minHeight: 38),
            visualDensity: VisualDensity.compact,
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(vertical: 6.0),
              decoration: BoxDecoration(
                color: isDark ? BssColors.darkOakBg : BssColors.parchmentBg,
                border: Border(bottom: BorderSide(color: goldColor.withAlpha(76), width: 1.0)),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8.0),
                    child: SizedBox(
                    height: 32,
                    child: Row(
                      children: [
                        for (int index = 0; index < _mainPeriods.length; index++)
                          Expanded(
                            child: Builder(builder: (context) {
                              final period = _mainPeriods[index];
                              final isSelected = (period.id == _selectedMainPeriodId);

                              return Padding(
                                padding: const EdgeInsets.symmetric(horizontal: 2.0),
                                child: GestureDetector(
                                  onTap: () => _onMainPeriodTabSelected(period.id),
                                  child: AnimatedContainer(
                                    duration: const Duration(milliseconds: 180),
                                    decoration: BoxDecoration(
                                      color: isSelected ? goldColor : cardBg,
                                      borderRadius: BorderRadius.circular(6.0),
                                      border: Border.all(color: goldColor, width: 1.0),
                                    ),
                                    child: Center(
                                      child: Text(
                                        '${index + 1}',
                                        style: TextStyle(
                                          fontSize: 13,
                                          fontWeight: FontWeight.bold,
                                          color: isSelected ? (isDark ? BssColors.darkOakBg : Colors.white) : textColor,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              );
                            }),
                          ),
                      ],
                    ),
                  ),
                  ),
                  if (_currentSubPeriods.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    SizedBox(
                      height: 34,
                      child: ListView.builder(
                        controller: _subPeriodScrollController,
                        scrollDirection: Axis.horizontal,
                        itemCount: _currentSubPeriods.length,
                        padding: const EdgeInsets.symmetric(horizontal: 8.0),
                        itemBuilder: (context, index) {
                          final sub = _currentSubPeriods[index];
                          final isSelected = (sub.id == _selectedSubPeriodId);

                          return GestureDetector(
                            onTap: () => _onSubPeriodSelected(sub.id),
                            child: AnimatedContainer(
                              duration: const Duration(milliseconds: 180),
                              padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 6.0),
                              margin: const EdgeInsets.symmetric(horizontal: 2.0),
                              decoration: BoxDecoration(
                                color: isSelected ? goldColor.withAlpha(64) : Colors.transparent,
                                borderRadius: BorderRadius.circular(14.0),
                                border: Border.all(color: isSelected ? goldColor : goldColor.withAlpha(76), width: 1.0),
                              ),
                              child: Center(
                                child: Text(
                                  sub.timeRange.isNotEmpty ? sub.timeRange : '${index + 1}',
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                    color: isSelected ? goldColor : textColor,
                                  ),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ],
              ),
            ),
            Expanded(
              child: Stack(
                children: [
                  ValueListenableBuilder<double>(
                    valueListenable: AppSettings.fontScale,
                    builder: (context, scale, child) {
                      return MediaQuery(
                        data: MediaQuery.of(context).copyWith(
                          textScaler: TextScaler.linear(scale),
                        ),
                        child: child!,
                      );
                    },
                    child: ScrollablePositionedList.builder(
                    itemScrollController: _itemScrollController,
                    itemPositionsListener: _itemPositionsListener,
                    padding: const EdgeInsets.only(left: 12.0, right: 64.0, top: 8.0, bottom: 24.0),
                    itemCount: _feedItems.length,
                    itemBuilder: (context, index) {
                      final item = _feedItems[index];

                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 10.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            if (index > 0 && item.isFirstInSubPeriod) ...[
                              Divider(color: goldColor.withAlpha(90), thickness: 1.0),
                              const SizedBox(height: 6),
                            ],
                            if (item.isFirstInMainPeriod) ...[
                              Text(
                                '${_mainPeriods.indexWhere((p) => p.id == item.mainPeriod.id) + 1} ${item.mainPeriod.title}',
                                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: goldColor),
                              ),
                              const SizedBox(height: 4),
                            ],
                            if (item.isFirstInSubPeriod) ...[
                              Text(
                                item.subPeriod.timeRange.isNotEmpty
                                    ? '${item.subPeriod.title} · ${item.subPeriod.timeRange}'
                                    : item.subPeriod.title,
                                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: textColor),
                              ),
                              const SizedBox(height: 6),
                            ],
                            Text(
                              item.section.title,
                              style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: textColor),
                            ),
                            if (item.section.hindiHeading.isNotEmpty) ...[
                              const SizedBox(height: 3),
                              Text(
                                item.section.hindiHeading,
                                style: TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: goldColor),
                              ),
                            ],
                            const SizedBox(height: 8),
                            ...item.verses.map((verse) {
                              final displayRef = verse.bookId != null
                                  ? verse.refDisplay
                                  : Translations.translateSourceRef(verse.sourceRefs);
                              return Padding(
                              key: verse.verseId == _highlightedVerseId ? _highlightedQuoteKey : null,
                              padding: const EdgeInsets.only(bottom: 8.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  _buildVerseText(verse, textColor, goldColor),
                                  // Source verses show their book ref; BSS verses
                                  // show source_refs (the scriptures they cite).
                                  if (displayRef.isNotEmpty) ...[
                                    const SizedBox(height: 3),
                                    Align(
                                      alignment: Alignment.centerRight,
                                      child: GestureDetector(
                                        onTap: verse.bookId != null
                                            ? (verse.verseId > 0
                                                ? () => _openVerseDetail(verse.verseId)
                                                : null)
                                            : (verse.sourceRefs.isNotEmpty
                                                ? () => _openSourceRefVerse(verse.sourceRefs)
                                                : null),
                                        child: Text(
                                          displayRef,
                                          style: TextStyle(
                                            fontSize: 11,
                                            fontStyle: FontStyle.italic,
                                            color: goldColor,
                                            decoration: (verse.bookId != null && verse.verseId > 0) ||
                                                    (verse.bookId == null && verse.sourceRefs.isNotEmpty)
                                                ? TextDecoration.underline
                                                : TextDecoration.none,
                                            decorationColor: goldColor.withAlpha(140),
                                          ),
                                        ),
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                              );
                            }),
                          ],
                        ),
                      );
                    },
                  ),
                  ),
                  Positioned(
                    right: 0,
                    top: 0,
                    bottom: 0,
                    child: Container(
                      width: 52,
                      padding: const EdgeInsets.symmetric(vertical: 6.0, horizontal: 2.0),
                      decoration: BoxDecoration(
                        color: (isDark ? BssColors.darkOakCard : BssColors.parchmentCard).withAlpha(240),
                        border: Border(left: BorderSide(color: goldColor.withAlpha(102), width: 1.0)),
                      ),
                      child: Column(
                        children: [
                          Text('${activeRailItems.length}', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: goldColor)),
                          const Divider(height: 8),
                          Expanded(
                            child: ListView.builder(
                              itemCount: activeRailItems.length,
                              padding: EdgeInsets.zero,
                              itemBuilder: (context, idx) {
                                final railItem = activeRailItems[idx];
                                final isSelected = (railItem.section.id == _selectedSectionId);

                                return GestureDetector(
                                  onTap: () => _onSectionRailSelected(railItem.section.id),
                                  child: Container(
                                    margin: const EdgeInsets.symmetric(vertical: 4.0),
                                    alignment: Alignment.center,
                                    child: AnimatedContainer(
                                      duration: const Duration(milliseconds: 180),
                                      width: 28,
                                      height: 28,
                                      decoration: BoxDecoration(
                                        shape: BoxShape.circle,
                                        color: isSelected ? goldColor : Colors.transparent,
                                        border: Border.all(color: goldColor, width: 1.2),
                                      ),
                                      child: Center(
                                        child: Text(
                                          '${idx + 1}',
                                          style: TextStyle(
                                            fontSize: 11,
                                            fontWeight: FontWeight.bold,
                                            color: isSelected ? (isDark ? BssColors.darkOakBg : Colors.white) : textColor,
                                          ),
                                        ),
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
