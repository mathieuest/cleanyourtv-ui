"""Exercise the UI's real language dispatch and French copy on the JVM (no TV or secrets)."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "launcher-ui/app/src/io/cleanyourtv/ui"


class FrenchUiTest(unittest.TestCase):
    def test_language_dispatch_and_dates(self):
        sdk = Path(os.environ.get("ANDROID_HOME", Path.home() / "Library/Android/sdk"))
        jars = sorted(sdk.glob("platforms/android-*/android.jar"))
        java_home = Path(os.environ.get("JAVA_HOME", "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"))
        javac = str(java_home / "bin/javac") if (java_home / "bin/javac").is_file() else shutil.which("javac")
        java = str(java_home / "bin/java") if (java_home / "bin/java").is_file() else shutil.which("java")
        if not jars or not javac or not java:
            self.skipTest("Android SDK and JDK required for the UI JVM test")
        with tempfile.TemporaryDirectory() as folder:
            tmp = Path(folder)
            # Only Android's drawing containers and preferences are replaced: no drawing or Android runtime here.
            stubs = {
                "Rect.java": "package android.graphics; public class Rect { public int top, left; }",
                "RectF.java": "package android.graphics; public class RectF { public void set(float a,float b,float c,float d){} }",
                "Prefs.java": 'package io.cleanyourtv.ui; final class Prefs { static String value="auto"; static String language(){return value;} }',
                "FrenchCheck.java": '''package io.cleanyourtv.ui;
import java.util.*;
public class FrenchCheck {
    static void eq(Object want, Object got) {
        if (!want.equals(got)) throw new AssertionError("Expected " + want + "; got " + got);
    }
    public static void main(String[] args) {
        TimeZone.setDefault(TimeZone.getTimeZone("UTC"));
        Locale.setDefault(Locale.FRANCE);
        Ui.applyLanguage();
        eq("fr", Ui.language);
        eq("Toutes les applications", Ui.tr("Todos os apps", "All Apps"));
        eq("Paramètres", Ui.tr("Ajustes", "Settings", "Ajustes"));
        Calendar date = new GregorianCalendar(2026, Calendar.OCTOBER, 23, 21, 7);
        eq("21:07", Ui.clock(date.getTimeInMillis()));
        eq("vendredi 23 octobre", Ui.date(date.getTimeInMillis()));
        Locale.setDefault(Locale.CANADA_FRENCH);
        Ui.applyLanguage();
        eq(Locale.CANADA_FRENCH, Ui.locale());
        Locale.setDefault(Locale.JAPAN);
        Prefs.value = "fr";
        Ui.applyLanguage();
        eq(Locale.FRANCE, Ui.locale());
        eq("Pour vous", Ui.tr("Para você", "For You"));
        eq("Unmapped brand name", French.text("Unmapped brand name"));
        eq("Effacer", French.text("Clear"));
        eq("Sons de navigation", Ui.tr("Sons de navegação", "Navigation sounds"));
        eq("N° 2 des séries du jour", French.text("No. 2 in shows today"));
        eq("il y a 1 jour", French.text("1 days ago"));
        eq("il y a 2 jours", French.text("2 days ago"));
        eq("Mot-clé « ", French.text("Tagged “"));
        Prefs.value = "en";
        Ui.applyLanguage();
        eq("All Apps", Ui.tr("Todos os apps", "All Apps"));
        Prefs.value = "auto";
        Ui.applyLanguage();
        eq("en", Ui.language);
    }
}''',
            }
            for name, contents in stubs.items():
                (tmp / name).write_text(contents, encoding="utf-8")
            files = [str(SOURCE / (name + ".java")) for name in ("Ui", "French", "Spanish", "German", "Russian")]
            compiled = subprocess.run([javac, "-encoding", "UTF-8", "-cp", str(jars[-1]), "-d", folder,
                                       *files, *(str(tmp / name) for name in stubs)], capture_output=True, text=True)
            self.assertEqual(0, compiled.returncode, compiled.stderr)
            checked = subprocess.run([java, "-cp", os.pathsep.join([folder, str(jars[-1])]),
                                      "io.cleanyourtv.ui.FrenchCheck"], capture_output=True, text=True)
            self.assertEqual(0, checked.returncode, checked.stderr)


if __name__ == "__main__":
    unittest.main()
