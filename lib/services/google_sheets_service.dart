import 'dart:convert';
import 'dart:developer';
import 'dart:io';
import 'package:flutter/services.dart' show rootBundle;
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

class GoogleSheetsService {
  final String apiKey = "AIzaSyBu1Jn1O8RDAe1SFNFwaBr2Sozw5qUmZ9Y"; // Replace with your API Key
  final String spreadsheetId = "1BOi13OBrITCVjbHY5osOJFZs4lp0gMVYQCFdRWzrpHY"; // Replace with your Spreadsheet ID

  // In-memory cache
  final Map<String, List<Map<String, dynamic>>> _cache = {};

  Future<List<Map<String, dynamic>>> loadData(String sheetName, {bool forceReload = false}) async {
    try {
      // Use cached data if available and forceReload is false
      if (!forceReload && _cache.containsKey(sheetName)) {
        log("Loading cached data for $sheetName");
        return _cache[sheetName]!;
      }

      // Attempt to load local data
      final localData = await _loadLocalData(sheetName);
      if (localData.isNotEmpty) {
        _cache[sheetName] = localData; // Cache the local data
        log("Loaded local data for $sheetName");
        return localData;
      }

      // If forceReload or no local data, fetch remote data
      if (forceReload || localData.isEmpty) {
        final onlineData = await _fetchSheetData(sheetName);
        _cache[sheetName] = onlineData; // Cache the fetched data
        return onlineData;
      }

      log("No local or online data available for $sheetName.");
      return [];
    } catch (e) {
      log("Error loading data for $sheetName: $e");
      return [];
    }
  }

  Future<List<String>> fetchSheetNames() async {
    final url =
        'https://sheets.googleapis.com/v4/spreadsheets/$spreadsheetId?fields=sheets.properties.title&key=$apiKey';
    try {
      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final sheets = data['sheets'] as List<dynamic>;
        return sheets.map<String>((sheet) => sheet['properties']['title'] as String).toList();
      } else {
        throw Exception('Error loading sheet names: ${response.statusCode}');
      }
    } catch (e) {
      log("Error fetching sheet names: $e");
      rethrow;
    }
  }

  Future<void> downloadAllSheets() async {
    try {
      final sheetNames = await fetchSheetNames();
      log("Fetching sheet names: $sheetNames");

      for (final sheetName in sheetNames) {
        log("Starting download for sheet: $sheetName");
        final data = await _fetchSheetData(sheetName);

        if (data.isNotEmpty) {
          log("Downloaded ${data.length} rows for sheet: $sheetName");
        } else {
          log("No data found for sheet: $sheetName");
        }

        _cache[sheetName] = data; // Update cache
      }
      log("Downloaded all sheets successfully.");
    } catch (e) {
      log("Error downloading sheets: $e");
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> _fetchSheetData(String sheetName) async {
    final url =
        'https://sheets.googleapis.com/v4/spreadsheets/$spreadsheetId/values/$sheetName?key=$apiKey';
    try {
      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final rows = data['values'] as List<dynamic>;

        if (rows.isEmpty) return [];

        final headers = List<String>.from(rows[0]); // First row as headers
        final parsedData = rows.skip(1).map((row) {
          final Map<String, dynamic> entry = {};
          for (int i = 0; i < headers.length; i++) {
            entry[headers[i]] = i < row.length ? row[i] : null;
          }
          return entry;
        }).toList();

        // Save fetched data locally
        await _saveLocalData(sheetName, parsedData);
        return parsedData;
      } else {
        throw Exception('Error fetching sheet data: ${response.statusCode}');
      }
    } catch (e) {
      log("Error fetching data for $sheetName: $e");
      return [];
    }
  }

Future<List<Map<String, dynamic>>> _loadLocalData(String sheetName) async {
  try {
    final directory = await getApplicationDocumentsDirectory();
    final path = '${directory.path}/contacts_$sheetName.json';

    // Check for local file
    if (File(path).existsSync()) {
      final jsonData = await File(path).readAsString();
      final data = json.decode(jsonData);

      if (data is List) {
        log("Loaded ${data.length} rows from local file for $sheetName.");
        return data.map((e) => Map<String, dynamic>.from(e)).toList();
      } else if (data is Map && data.containsKey('values')) {
        final rows = data['values'] as List<dynamic>;
        if (rows.isEmpty) return [];

        final headers = List<String>.from(rows[0]); // First row as headers
        return rows.skip(1).map((row) {
          final Map<String, dynamic> entry = {};
          for (int i = 0; i < headers.length; i++) {
            entry[headers[i]] = i < row.length ? row[i] : null;
          }
          return entry;
        }).toList();
      } else {
        log("Unexpected format in local file for $sheetName.");
        return [];
      }
    } else {
      log("No local file found for $sheetName. Falling back to assets.");
    }

    // Fallback to assets if local file is missing
    final assetJson = await rootBundle.loadString('assets/data/contacts_$sheetName.json');
    final data = json.decode(assetJson);

    if (data is List) {
      log("Loaded ${data.length} rows from assets for $sheetName.");
      return data.map((e) => Map<String, dynamic>.from(e)).toList();
    } else if (data is Map && data.containsKey('values')) {
      final rows = data['values'] as List<dynamic>;
      if (rows.isEmpty) return [];

      final headers = List<String>.from(rows[0]); // First row as headers
      return rows.skip(1).map((row) {
        final Map<String, dynamic> entry = {};
        for (int i = 0; i < headers.length; i++) {
          entry[headers[i]] = i < row.length ? row[i] : null;
        }
        return entry;
      }).toList();
    } else {
      log("Unexpected format in assets file for $sheetName.");
      return [];
    }
  } catch (e) {
    log("Error loading local data for $sheetName: $e");
    return [];
  }
}


  Future<void> _saveLocalData(String sheetName, List<Map<String, dynamic>> data) async {
    try {
      final directory = await getApplicationDocumentsDirectory();
      final path = '${directory.path}/contacts_$sheetName.json';
      final file = File(path);
      final content = json.encode(data);
      await file.writeAsString(content, flush: true);
      log("Data saved for $sheetName: ${data.length} rows.");
    } catch (e) {
      log("Error saving data for $sheetName: $e");
    }
  }

  Future<bool> isConnectedToInternet() async {
    try {
      final result = await http.get(Uri.parse('https://www.google.com')).timeout(const Duration(seconds: 3));
      return result.statusCode == 200;
    } catch (e) {
      log("Internet connectivity check failed: $e");
      return false;
    }
  }
  // Load app state
  Future<String> loadState() async {
      try {
        final directory = await getApplicationDocumentsDirectory();
        final path = '${directory.path}/app_state.json';
        final file = File(path);

        if (await file.exists()) {
          String content = await file.readAsString();
          Map<String, dynamic> jsonData = json.decode(content);
          return jsonData['route'] ?? '/';
        }
      } catch (e) {
        print('Error loading state: $e');
      }
      return '/';
    }
  void clearCache() {
    _cache.clear();
    log("Cache cleared.");
  }
  Future<void> updateData() async {
    if (await isConnectedToInternet()) {
      await downloadAllSheets();
    } else {
      log("No internet connection. Using local data.");
    }
  }
}
