# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307
# USA
#
# Author(s): Ali Afshar <aafshar@gmail.com>
#

"""FontButton proxy for the kiwi framework"""

from gi.repository import Gtk

from kiwi.ui.proxywidget import ProxyWidgetMixin
from kiwi.utils import type_register


class ProxyFontButton(Gtk.FontButton, ProxyWidgetMixin):
    __gtype_name__ = 'ProxyFontButton'

    allowed_data_types = str,

    def __init__(self, fontname=None):
        ProxyWidgetMixin.__init__(self)
        Gtk.FontButton.__init__(self, fontname)
        self.props.data_type = str

    def do_font_set(self):
        self.emit('content-changed')

    def read(self):
        return self.get_font_name()

    def update(self, data):
        self.set_font_name(data)

type_register(ProxyFontButton)
