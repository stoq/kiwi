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

import gtk

from kiwi.ui.proxywidget import ProxyWidgetMixin
from kiwi.utils import gsignal, type_register


class ProxyFontButton(gtk.FontButton, ProxyWidgetMixin):
    __gtype_name__ = 'ProxyFontButton'

    allowed_data_types = basestring,

    def __init__(self, fontname=None):
        ProxyWidgetMixin.__init__(self)
        gtk.FontButton.__init__(self, fontname)
        self.props.data_type = str

    gsignal('font-set', 'override')
    def do_font_set(self):
        self.emit('content-changed')
        self.chain()

    def read(self):
        return self.get_font_name()

    def update(self, data):
        self.set_font_name(data)

type_register(ProxyFontButton)

