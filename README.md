#webvtt.py

A cgi-script written in Python to export professional EBU-STL subtitles as WebVTT file format with optional formatting.
WebVTT is the [W3C](http://www.w3c.org) sanctioned and widely used subtitle format.

This conversions can be optionally done while preserving as much formatting as possible. The output formatting is done using CSS classes and the following attributes are supported:

* bold
* italic
* underlined
* color (foreground and background)
* boxing
* alignment

In addition it decodes all STL header metadata fields as WebVTT notes at the beginning of the output.


## Usage
  
`webvtt.py` (called by cgi)

HTTP GET params
>  `file`<br/>
>  STL source filename
>
>  `starttc`<br/>
>  Timecode in seconds to substract from STL internal timecode to match start of video
>  Example: STL first timecode is 10h 00m 00s 00f, start of video is 0.0s
>  => starttc should be set to 36000.0 to match video and subtitle


## Bibliography

* The file format specifications are available at:
	* [EBU STL spec (PDF)](http://tech.ebu.ch/docs/tech/tech3264.pdf)
	* [W3C Time Text reference](http://www.w3.org/TR/2010/REC-ttaf1-dfxp-20101118/)


## License

Starting with version 2.1 released on September 22nd, 2014, this software is now released under the Apache License, Version 2.0

You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Previous versions, up to 2.0.8, were licensed under the GPL v2 terms and conditions.
