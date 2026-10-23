"""Run real Click methods against a recording audio backend, without Android or a TV."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "launcher-ui/app/src/io/cleanyourtv/ui"


class NavigationSoundsTest(unittest.TestCase):
    def test_audio_obeys_current_preference(self):
        home = Path(os.environ.get("JAVA_HOME", "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"))
        javac = str(home / "bin/javac") if (home / "bin/javac").is_file() else shutil.which("javac")
        java = str(home / "bin/java") if (home / "bin/java").is_file() else shutil.which("java")
        if not javac or not java:
            self.skipTest("JDK required for audio JVM test")
        with tempfile.TemporaryDirectory() as folder:
            tmp = Path(folder)
            stubs = {
                "Context.java": '''package android.content;
public class Context { public java.io.File getCacheDir(){ return new java.io.File(System.getProperty("java.io.tmpdir")); } }''',
                "AudioAttributes.java": '''package android.media;
public class AudioAttributes {
 public static final int USAGE_ASSISTANCE_SONIFICATION=13, CONTENT_TYPE_SONIFICATION=4;
 public static class Builder {
  public Builder setUsage(int v){return this;} public Builder setContentType(int v){return this;}
  public AudioAttributes build(){return new AudioAttributes();}
 }
}''',
                "SoundPool.java": '''package android.media;
public class SoundPool {
 public static int plays;
 public static class Builder {
  public Builder setMaxStreams(int v){return this;} public Builder setAudioAttributes(AudioAttributes a){return this;}
  public SoundPool build(){return new SoundPool();}
 }
 public int load(String file,int priority){return 1;}
 public int play(int id,float left,float right,int priority,int loop,float rate){plays++;return plays;}
 public void release(){}
}''',
                "Prefs.java": '''package io.cleanyourtv.ui;
final class Prefs { static boolean enabled=true; static boolean navigationSounds(){return enabled;} }''',
                "AppLog.java": '''package io.cleanyourtv.ui; final class AppLog { static void w(String m){} }''',
                "NavigationSoundsCheck.java": '''package io.cleanyourtv.ui;
import android.media.SoundPool;
public class NavigationSoundsCheck {
 static void plays(int expected) {
  if(SoundPool.plays!=expected)throw new AssertionError("Expected "+expected+" sounds, got "+SoundPool.plays);
 }
 public static void main(String[] args) {
  Click click=new Click(new android.content.Context());
  click.move();click.open();plays(2);
  Prefs.enabled=false;
  click.move();click.open();plays(2);
  Prefs.enabled=true;
  click.move();click.open();plays(4);
  click.release();click.move();click.open();plays(4);
 }
}''',
            }
            for name, contents in stubs.items():
                (tmp / name).write_text(contents, encoding="utf-8")
            compiled = subprocess.run([javac, "-encoding", "UTF-8", "-d", folder, str(SOURCE / "Click.java"),
                                       *(str(tmp / name) for name in stubs)], capture_output=True, text=True)
            self.assertEqual(0, compiled.returncode, compiled.stderr)
            checked = subprocess.run([java, "-Djava.io.tmpdir=" + folder, "-cp", folder,
                                      "io.cleanyourtv.ui.NavigationSoundsCheck"], capture_output=True, text=True)
            self.assertEqual(0, checked.returncode, checked.stderr)


if __name__ == "__main__":
    unittest.main()
